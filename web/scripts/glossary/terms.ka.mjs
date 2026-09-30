import scopes from "./part-scopes.ka.mjs";
import bullets from "./part-bullets.ka.mjs";
import charts from "./part-charts.ka.mjs";
import environment from "./part-environment.ka.mjs";

export const CATEGORIES = ["საფუძვლები", "ოპტიკა და შესწორებები", "ბალისტიკური ცხრილები", "ტრაექტორია და ნული", "ტყვია და წინაღობა", "ქარი და გარემო"];
export default (H) => [...scopes(H), ...bullets(H), ...charts(H), ...environment(H)];
