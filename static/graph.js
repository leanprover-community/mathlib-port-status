// from https://codepen.io/brinkbot/pen/oNZJXqK
function make_graph(svgNode, data){
  const dag = d3.dagConnect()(data);
  const nodeHeight = 24;
  const charWidth = 9.5;
  const nodeMargin = 30;
  const layout = d3
    .sugiyama() // base layout
    // .decross(d3.decrossOpt()) // minimize number of crossings
    .nodeSize((node) => node ? [node.data.id.length * charWidth + nodeMargin, nodeHeight + nodeMargin] : [nodeMargin, nodeMargin]); // set node size
  const { width, height } = layout(dag);


  const svgSelection = d3.select(svgNode);
  const rootSelection = svgSelection.append('g');
  let zoom = d3.zoom().on('zoom', handleZoom);
  function handleZoom(e) {
    rootSelection.attr('transform', e.transform);
  }

  svgSelection.call(zoom);
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
  rootSelection
    .append("g")
    .attr("mask", "url(#nodeMask)")
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
  const nodes = rootSelection
    .append("g")
    .selectAll("g")
    .data(dag.descendants())
    .enter()
    .append("a")
    .style("text-decoration", "none")
    .attr("href", d => "file/" + d.data.id.replace(/\./g, "/"))
    .attr("transform", ({ x, y }) => `translate(${x}, ${y})`);

  const nodeMaskRoot = rootSelection.append("mask").attr('id', 'nodeMask');
  nodeMaskRoot.append("rect")
    .attr("width", "100%")
    .attr("height", "100%")
    .attr("fill", "white");
  const nodeMask = nodeMaskRoot
    .append("g")
    .selectAll("g")
    .data(dag.descendants())
    .enter()
    .append("g")
    .attr("transform", ({ x, y }) => `translate(${x}, ${y})`);

  // Plot node boces
  nodes
    .append("rect")
    .attr("x", (n) => -charWidth*n.data.id.length / 2)
    .attr("width", (n) => charWidth*n.data.id.length)
    .attr("y", -nodeHeight/2)
    .attr("height", nodeHeight)
    .attr("rx", "0.375rem")
    .attr("fill", (n) => d3.color(colorMap.get(n.data.id)).copy({opacity: 0.5}));

  nodeMask
    .append("rect")
    .attr("x", (n) => -charWidth*n.data.id.length / 2)
    .attr("width", (n) => charWidth*n.data.id.length)
    .attr("y", -nodeHeight/2)
    .attr("height", nodeHeight)
    .attr("rx", "0.375rem")
    .attr("fill", "black");

  // Add text to nodes
  nodes
    .append("text")
    .text((d) => d.data.id)
    .attr("class", "font-monospace")
    .attr("text-anchor", "middle")
    .attr("alignment-baseline", "middle")
    .style("fill", "var(--bs-emphasis-color)");
}