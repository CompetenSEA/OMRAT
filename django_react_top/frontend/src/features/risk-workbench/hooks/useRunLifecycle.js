import { useCallback, useState } from 'react';

/**
 * Run lifecycle hook that mirrors backend enqueue/execute/poll semantics.
 */
export function useRunLifecycle(client, dispatch) {
  const [running, setRunning] = useState(false);

  const startRun = useCallback(async (payload) => {
    setRunning(true);
    try {
      const queued = await client.enqueueRun(payload);
      dispatch({ type: 'RUN_QUEUED', task: queued });

      const executing = await client.executeRun(queued.task_id);
      dispatch({ type: 'RUN_PROGRESS', task: executing });

      const completed = await client.getTask(queued.task_id);
      if (completed.state === 'completed') {
        dispatch({ type: 'RUN_COMPLETED', task: completed });
      } else {
        dispatch({ type: 'RUN_PROGRESS', task: completed });
      }
    } finally {
      setRunning(false);
    }
  }, [client, dispatch]);

  return {
    running,
    startRun,
  };
}
