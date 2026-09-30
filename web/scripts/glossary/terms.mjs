import scopes from "./part-scopes.mjs";
import bullets from "./part-bullets.mjs";
import charts from "./part-charts.mjs";
import environment from "./part-environment.mjs";

export const CATEGORIES = ["Getting started", "Scopes and adjustments", "Ballistic charts", "Trajectory and zeroing", "Bullets and drag", "Wind and environment"];
export default (H) => [...scopes(H), ...bullets(H), ...charts(H), ...environment(H)];
