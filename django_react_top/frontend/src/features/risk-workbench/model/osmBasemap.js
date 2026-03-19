/**
 * OSM XYZ tile helpers for lightweight map underlay rendering.
 * Assumes input coordinates are WGS84 lon/lat pairs.
 */

const TILE_SIZE = 256;

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

export function isLikelyLonLatBounds(bounds) {
  if (!bounds) return false;
  return (
    Number.isFinite(bounds.minX)
    && Number.isFinite(bounds.maxX)
    && Number.isFinite(bounds.minY)
    && Number.isFinite(bounds.maxY)
    && bounds.minX >= -180
    && bounds.maxX <= 180
    && bounds.minY >= -85.0511
    && bounds.maxY <= 85.0511
  );
}

export function lonLatToPixel(lon, lat, zoom) {
  const z = Math.max(0, Math.floor(Number(zoom) || 0));
  const scale = TILE_SIZE * (2 ** z);
  const clampedLat = clamp(lat, -85.0511, 85.0511);
  const x = ((lon + 180) / 360) * scale;
  const latRad = (clampedLat * Math.PI) / 180;
  const y = (0.5 - (Math.log((1 + Math.sin(latRad)) / (1 - Math.sin(latRad))) / (4 * Math.PI))) * scale;
  return { x, y };
}

export function buildOsmTileViewport(bounds, zoom = 6, maxTiles = 48) {
  if (!isLikelyLonLatBounds(bounds)) {
    return { tiles: [], width: 1, height: 1, minPixelX: 0, minPixelY: 0 };
  }

  const nw = lonLatToPixel(bounds.minX, bounds.maxY, zoom);
  const se = lonLatToPixel(bounds.maxX, bounds.minY, zoom);

  const minTileX = Math.floor(nw.x / TILE_SIZE);
  const minTileY = Math.floor(nw.y / TILE_SIZE);
  const maxTileX = Math.floor(se.x / TILE_SIZE);
  const maxTileY = Math.floor(se.y / TILE_SIZE);

  const tileCount = (maxTileX - minTileX + 1) * (maxTileY - minTileY + 1);
  if (tileCount <= 0 || tileCount > maxTiles) {
    return { tiles: [], width: se.x - nw.x || 1, height: se.y - nw.y || 1, minPixelX: nw.x, minPixelY: nw.y };
  }

  const tiles = [];
  for (let x = minTileX; x <= maxTileX; x += 1) {
    for (let y = minTileY; y <= maxTileY; y += 1) {
      tiles.push({
        key: `tile-${zoom}-${x}-${y}`,
        x,
        y,
        z: zoom,
        left: (x * TILE_SIZE) - nw.x,
        top: (y * TILE_SIZE) - nw.y,
        url: `https://tile.openstreetmap.org/${zoom}/${x}/${y}.png`,
      });
    }
  }

  return {
    tiles,
    width: Math.max(1, se.x - nw.x),
    height: Math.max(1, se.y - nw.y),
    minPixelX: nw.x,
    minPixelY: nw.y,
  };
}
