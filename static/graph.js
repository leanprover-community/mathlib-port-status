// from https://codepen.io/brinkbot/pen/oNZJXqK
function make_graph(svgNode, edgeData, nodeData){
  const dag = d3.dagConnect().nodeDatum(id => ({ id, state: nodeData[id]}))(edgeData);
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
  svgSelection.attr("height", height);
  svgSelection.attr("viewBox", [0, 0, width, height].join(" "));

  // How to draw edges
  const line = d3
    .line()
    .curve(d3.curveCatmullRom)
    .x((d) => d.x)
    .y((d) => d.y);

  // Plot edges
  const edges = rootSelection
    .append("g")
    .attr("mask", "url(#nodeMask)")
    .selectAll("path")
    .data(dag.links())
    .enter()
    .append("path")
    .attr("d", ({ points }) => line(points))
    .attr("fill", "none")
    .attr("stroke-width", 3)
    .style("stroke", "var(--bs-tertiary-color)");

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

  const nodeMaskRoot = rootSelection.append("mask")
    .attr('id', 'nodeMask')
    .attr("maskUnits", "userSpaceOnUse");
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

  nodes
    .append("title").text((n) =>
      n.data.state == 'PORTED' ? "ported" :
      n.data.state == 'IN_PROGRESS' ? "in progress" : null);

  // Plot node boces
  nodes
    .append("rect")
    .attr("x", (n) => -charWidth*n.data.id.length / 2)
    .attr("width", (n) => charWidth*n.data.id.length)
    .attr("y", -nodeHeight/2)
    .attr("height", nodeHeight)
    .attr("rx", "0.375rem")
    .attr("fill", (n) =>
      n.data.state == 'PORTED' ? "var(--bs-success-bg-subtle)" :
      n.data.state == 'IN_PROGRESS' ? "var(--bs-warning-bg-subtle)" :
      "var(--bs-tertiary-bg)")
    .style("stroke", (n) =>
      n.data.state == 'PORTED' ? "var(--bs-success-border-subtle)" :
      n.data.state == 'IN_PROGRESS' ? "var(--bs-warning-border-subtle)" :
      "var(--bs-tertiary-color)");
  nodes
    .each(function(n) {
      svgNode.addEventListener('importset', e => {
        let which = e.detail;
        if (which.target == null) {
          d3.select(this).transition().duration(250).style('opacity', '1');
        }
        else if (which.descendants.includes(n)) {
          d3.select(this).transition().duration(250).style('opacity', '1');
        }
        else if (n.descendants().includes(which.target)) {
          d3.select(this).transition().duration(250).style('opacity', '1');
        }
        else {
          d3.select(this).transition().duration(250).style('opacity', '0.25');
        }
      })
    });
  edges
    .each(function(n) {
      svgNode.addEventListener('importset', e => {
        let which = e.detail;
        if (which.target == null) {
          d3.select(this).transition().duration(250).style('opacity', '1');
        }
        else if (which.descendants.includes(n.target) && which.descendants.includes(n.source)) {
          d3.select(this).transition().duration(250).style('opacity', '1');
        }
        else if (n.target.descendants().includes(which.target)) {
          d3.select(this).transition().duration(250).style('opacity', '1');
        }
        else {
          d3.select(this).transition().duration(250).style('opacity', '0.25');
        }
      })
    });

  nodes.on('mouseenter', function(e, n) {
    svgSelection.dispatch('importset', {detail:
      {target: n, descendants: n.descendants() }
    });
  })
  nodes.on('mouseleave', function(e, n) {
    svgSelection.dispatch('importset', {detail:
      {target: null, descendants: []}
    });
  })
  edges.on('mouseenter', function(e, n) {
    svgSelection.dispatch('importset', {detail:
      {target: n.source, descendants: n.source.descendants() }
    });
  })
  edges.on('mouseleave', function(e, n) {
    svgSelection.dispatch('importset', {detail:
      {target: null, descendants: []}
    });
  })

  nodeMask
    .append("rect")
    .attr("x", (n) => -charWidth*n.data.id.length / 2)
    .attr("width", (n) => charWidth*n.data.id.length)
    .attr("y", -nodeHeight/2)
    .attr("height", nodeHeight)
    .attr("rx", "0.375rem")
    .attr("fill", "black")
    .attr("stroke", "black");

  // Add text to nodes
  nodes
    .append("text")
    .text((d) => d.data.id)
    .attr("class", "font-monospace")
    .attr("text-anchor", "middle")
    .attr("alignment-baseline", "middle")
    .style("fill", n =>
      n.data.state == 'PORTED' ? "var(--bs-success-text)" :
      n.data.state == 'IN_PROGRESS' ? "var(--bs-warning-text)" :
      "var(--bs-emphasis-color)");
}
