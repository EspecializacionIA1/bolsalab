"use client";

import { useEffect, useState } from "react";

type Point = [number, number, number];

export type PieceShift = "none" | "small" | "large";

const PHI = (1 + Math.sqrt(5)) / 2;
const SIZE = 200;
const SCALE = 34;
const CAMERA = 6;
const TILT = 0.35;
const SPEED = 0.00025;
const PIECE_RADIUS = 0.75;

const vertices: Point[] = [
  [0, 1, PHI], [0, 1, -PHI], [0, -1, PHI], [0, -1, -PHI],
  [1, PHI, 0], [1, -PHI, 0], [-1, PHI, 0], [-1, -PHI, 0],
  [PHI, 0, 1], [PHI, 0, -1], [-PHI, 0, 1], [-PHI, 0, -1],
];

const edges = vertices.flatMap((a, i) =>
  vertices.slice(i + 1).flatMap((b, offset) => {
    const distance = Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]);
    return Math.abs(distance - 2) < 0.01 ? [[i, i + 1 + offset] as const] : [];
  }),
);

const shifts: Record<PieceShift, Point> = {
  none: [0, 0, 0],
  small: [0.35, 0.25, 0.2],
  large: [0.9, 0.7, 0.4],
};

const piece: Point[] = [0, 1, 2].map((index) => {
  const angle = (index * 2 * Math.PI) / 3 - Math.PI / 2;
  return [PIECE_RADIUS * Math.cos(angle), -PIECE_RADIUS * Math.sin(angle), 0];
});

function rotate([x, y, z]: Point, angle: number): Point {
  const x1 = x * Math.cos(angle) + z * Math.sin(angle);
  const z1 = -x * Math.sin(angle) + z * Math.cos(angle);
  const y2 = y * Math.cos(TILT) - z1 * Math.sin(TILT);
  const z2 = y * Math.sin(TILT) + z1 * Math.cos(TILT);
  return [x1, y2, z2];
}

function project([x, y, z]: Point) {
  const perspective = CAMERA / (CAMERA - z);
  return { x: SIZE / 2 + x * SCALE * perspective, y: SIZE / 2 - y * SCALE * perspective, depth: z };
}

function opacity(depth: number) {
  return 0.25 + (0.75 * (depth + PHI)) / (2 * PHI);
}

type WireFigureProps = {
  shift?: PieceShift;
  pieceStroke?: string;
  pieceFill?: string;
  cornerFills?: [string, string, string];
  label?: string;
};

export function WireFigure({
  shift = "none",
  pieceStroke = "stroke-holds",
  pieceFill = "fill-holds",
  cornerFills,
  label,
}: WireFigureProps) {
  const [angle, setAngle] = useState(0.6);

  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    let frame = 0;
    const start = performance.now();
    const tick = (now: number) => {
      setAngle(0.6 + (now - start) * SPEED);
      frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, []);

  const points = vertices.map((vertex) => project(rotate(vertex, angle)));
  const [cx, cy, cz] = rotate(shifts[shift], angle);
  const corners = piece.map(([x, y, z]) => project([x + cx, y + cy, z + cz]));

  return (
    <svg
      viewBox={`0 0 ${SIZE} ${SIZE}`}
      role={label ? "img" : undefined}
      aria-label={label}
      aria-hidden={label ? undefined : true}
      className="h-full w-full"
    >
      {edges.map(([a, b]) => (
        <line
          key={`${a}-${b}`}
          x1={points[a].x}
          y1={points[a].y}
          x2={points[b].x}
          y2={points[b].y}
          className="stroke-primary"
          strokeWidth={0.8}
          strokeOpacity={opacity((points[a].depth + points[b].depth) / 2)}
        />
      ))}
      <polygon
        points={corners.map((corner) => `${corner.x},${corner.y}`).join(" ")}
        className={`fill-none ${pieceStroke}`}
        strokeWidth={1.2}
      />
      {corners.map((corner, index) => (
        <circle
          key={index}
          cx={corner.x}
          cy={corner.y}
          r={cornerFills ? 4.5 : 2.2}
          className={cornerFills ? cornerFills[index] : pieceFill}
        />
      ))}
    </svg>
  );
}
