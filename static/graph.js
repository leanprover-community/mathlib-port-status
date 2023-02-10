// from https://codepen.io/brinkbot/pen/oNZJXqK
function make_graph(svgNode, data){
  const dag = d3.dagConnect()(data);
  const nodeHeight = 20;
  const charWidth = 10;
  const nodeMargin = 30;
  const layout = d3
    .sugiyama() // base layout
    // .decross(d3.decrossOpt()) // minimize number of crossings
    .nodeSize((node) => node ? [node.data.id.length * charWidth + nodeMargin * 2, nodeHeight + nodeMargin * 2] : [nodeHeight, nodeHeight]); // set node size 
  const { width, height } = layout(dag);

  const svgSelection = d3.select(svgNode);
  // svgSelection.attr("width", width);
  // svgSelection.attr("height", height);
  svgSelection.attr("viewBox", [0, 0, width, height].join(" "));
  const defs = svgSelection.append("defs"); // For gradients

  const steps = dag.size();
  const interp = d3.interpolateRainbow;
  const colorMap = new Map();
  let i = 0;
  for (const node of dag.idescendants()) {
    colorMap.set(node.data.id, interp(i++ / steps));
  }

  // How to draw edges
  const line = d3
    .line()
    .curve(d3.curveCatmullRom)
    .x((d) => d.x)
    .y((d) => d.y);

  // Plot edges
  svgSelection
    .append("g")
    .selectAll("path")
    .data(dag.links())
    .enter()
    .append("path")
    .attr("d", ({ points }) => line(points))
    .attr("fill", "none")
    .attr("stroke-width", 3)
    .attr("stroke", ({ source, target }) => {
      // encodeURIComponents for spaces, hope id doesn't have a `--` in it
      const gradId = encodeURIComponent(`${source.data.id}--${target.data.id}`);
      const grad = defs
        .append("linearGradient")
        .attr("id", gradId)
        .attr("gradientUnits", "userSpaceOnUse")
        .attr("x1", source.x)
        .attr("x2", target.x)
        .attr("y1", source.y)
        .attr("y2", target.y);
      grad
        .append("stop")
        .attr("offset", "0%")
        .attr("stop-color", colorMap.get(source.data.id));
      grad
        .append("stop")
        .attr("offset", "100%")
        .attr("stop-color", colorMap.get(target.data.id));
      return `url(#${gradId})`;
    });

  // Select nodes
  const nodes = svgSelection
    .append("g")
    .selectAll("g")
    .data(dag.descendants())
    .enter()
    .append("g")
    .attr("transform", ({ x, y }) => `translate(${x}, ${y})`);

  // Plot node circles
  nodes
    .append("rect")
    .attr("x", (n) => -charWidth*n.data.id.length / 2)
    .attr("width", (n) => charWidth*n.data.id.length)
    .attr("y", -nodeHeight/2)
    .attr("height", nodeHeight)
    .attr("fill", (n) => colorMap.get(n.data.id));

  // Add text to nodes
  nodes
    .append("text")
    .text((d) => d.data.id)
    .attr("class", "font-monospace")
    .attr("text-anchor", "middle")
    .attr("alignment-baseline", "middle")
    .attr("fill", "white");
}