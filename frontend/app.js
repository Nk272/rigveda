class HymnSimilarityMap 
{
    constructor() {
        console.log('Initializing HymnSimilarityMap...');
        this.width = window.innerWidth;
        this.height = window.innerHeight;
        this.nodes = new Map();
        this.links = new Map();
        this.pendingRequests = new Set();
        this.selectedNode = null;
        this.allNodes = [];
        this.focusNodeId = null;
        this.focusNeighborIds = new Set();
        this.isFocusMode = false;
        this.showLinks = false; // hide edges
        
        this.InitializeSvg();
        this.InitializeSimulation();
        this.InitializeTooltip();
        this.InitializeControls();
        this.InitializeSearch();
        this.LoadInitialData();
    }

    InitializeSvg() {
        console.log('Initializing SVG...');
        this.svg = d3.select("#graph")
            .attr("width", this.width)
            .attr("height", this.height);

        // Create zoom behavior
        this.zoom = d3.zoom()
            .scaleExtent([0.1, 4])
            .on("zoom", (event) => {
                this.container.attr("transform", event.transform);
            });

        this.svg.call(this.zoom);

        // Create container for graph elements
        this.container = this.svg.append("g");

        // Create groups for links and nodes
        this.linkGroup = this.container.append("g").attr("class", "links");
        this.nodeGroup = this.container.append("g").attr("class", "nodes");

        // Clear focus on canvas click
        this.svg.on("click", () => this.ClearFocusMode());
    }

    InitializeSimulation() {
        console.log('Initializing simulation...');
        this.simulation = d3.forceSimulation()
            .force("link", d3.forceLink()
                .id(d => d.id)
                .distance(d => 30 + (1 - (d.similarity || 0)) * 80)
                .strength(d => (d.similarity || 0) * 0.3)
            )
            .force("charge", d3.forceManyBody()
                .strength(-80)
                .distanceMax(300)
            )
            .force("center", d3.forceCenter(this.width / 2, this.height / 2).strength(0.05))
            .force("collision", d3.forceCollide()
                .radius(d => this.GetNodeRadius(d) + 2)
                .strength(0.7)
            );
    }

    InitializeTooltip() {
        this.tooltip = d3.select("body").append("div")
            .attr("class", "tooltip")
            .style("display", "none");
    }

    FocusViewportOnNode(node, scale = 2) {
        if (!node) return;
        const translate = [
            this.width / 2 - scale * node.x,
            this.height / 2 - scale * node.y
        ];
        this.svg.transition().duration(600).call(
            this.zoom.transform,
            d3.zoomIdentity.translate(translate[0], translate[1]).scale(scale)
        );
    }

    InitializeControls() {
        d3.select("#resetBtn").on("click", () => this.ResetView());
        d3.select("#centerBtn").on("click", () => this.CenterGraph());
        
        // Handle window resize
        window.addEventListener("resize", () => {
            this.width = window.innerWidth;
            this.height = window.innerHeight;
            this.svg.attr("width", this.width).attr("height", this.height);
            // this.simulation.force("center", d3.forceCenter(this.width / 2, this.height / 2));
            this.simulation.alpha(0.3).restart();
        });
    }

    InitializeSearch() {
        const searchInput = d3.select("#searchInput");
        const searchResults = d3.select("#searchResults");
        
        searchInput.on("input", () => {
            const query = searchInput.property("value").toLowerCase().trim();
            
            if (query.length < 2) {
                searchResults.style("display", "none");
                return;
            }
            
            const matches = this.allNodes.filter(node => 
                node.title.toLowerCase().includes(query) ||
                node.deity_names.toLowerCase().includes(query) ||
                `${node.book_number}.${node.hymn_number}`.includes(query)
            ).slice(0, 10);
            
            if (matches.length > 0) {
                const resultHtml = matches.map(node => 
                    `<div style="padding: 5px; cursor: pointer; border-bottom: 1px solid #333;" 
                          data-hymn-id="${node.id}">
                        <strong>${node.title}</strong><br>
                        <small>Book ${node.book_number}, Hymn ${node.hymn_number} - ${node.deity_names}</small>
                    </div>`
                ).join("");
                
                searchResults.html(resultHtml).style("display", "block");
                
                // Add click handlers to search results
                searchResults.selectAll("div").on("click", (event) => {
                    const hymnId = event.target.closest("div").getAttribute("data-hymn-id");
                    this.FocusOnNode(hymnId);
                    searchResults.style("display", "none");
                    searchInput.property("value", "");
                });
            } else {
                searchResults.html("<div style='padding: 10px; color: #999;'>No matches found</div>")
                    .style("display", "block");
            }
        });
        
        // Hide search results when clicking elsewhere
        document.addEventListener("click", (event) => {
            if (!event.target.closest("#controls")) {
                searchResults.style("display", "none");
            }
        });
    }

    async LoadInitialData() {
        try {
            console.log('Loading initial data...');
            d3.select("#loading").text("Loading all 1,028 hymns...");
            
            // Load all nodes for initial graph and search functionality
            const response = await fetch('/api/graph/initial');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            console.log(`Loaded ${data.nodes.length} nodes`);
            
            this.allNodes = data.nodes;
            
            // Position nodes with larger scores in center
            this.PositionNodesByScore(data.nodes);
            
            // Add all nodes to the map
            data.nodes.forEach(node => {
                this.nodes.set(node.id, node);
            });

            console.log(`Added ${this.nodes.size} nodes to visualization`);
            this.UpdateVisualization();
            
            d3.select("#loading").style("display", "none");
        } catch (error) {
            console.error('Error loading initial data:', error);
            d3.select("#loading").text(`Error: ${error.message}`);
        }
    }

    PositionNodesByScore(nodes) {
        console.log(`Positioning ${nodes.length} nodes by score`);
        
        // Sort nodes by hymn score (descending) - don't mutate original
        const sortedNodes = [...nodes].sort((a, b) => b.hymn_score - a.hymn_score);
        
        const centerX = this.width / 2;
        const centerY = this.height / 2;
        
        console.log(`Center position: ${centerX}, ${centerY}`);
        
        sortedNodes.forEach((node, index) => {
            if (index < 50) {
                // Top 50 nodes: position in tight center circle
                const angle = (index / 50) * 2 * Math.PI;
                const radius = 50 + (index / 50) * 100;
                node.x = centerX + Math.cos(angle) * radius;
                node.y = centerY + Math.sin(angle) * radius;
            } else if (index < 200) {
                // Next 150 nodes: middle ring
                const angle = ((index - 50) / 150) * 2 * Math.PI;
                const radius = 200 + ((index - 50) / 150) * 150;
                node.x = centerX + Math.cos(angle) * radius;
                node.y = centerY + Math.sin(angle) * radius;
            } else {
                // Remaining nodes: outer area with some randomness
                const angle = Math.random() * 2 * Math.PI;
                const radius = 400 + Math.random() * 300;
                node.x = centerX + Math.cos(angle) * radius;
                node.y = centerY + Math.sin(angle) * radius;
            }
            
            // Log first few positions for debugging
            if (index < 3) {
                console.log(`Node ${index} (${node.id}): x=${node.x.toFixed(1)}, y=${node.y.toFixed(1)}, score=${node.hymn_score}`);
            }
        });
    }

    GetNodeRadius(node) {
        const minRadius = 4;
        const maxRadius = 20;
        
        // Fallback if allNodes is not loaded yet
        if (!this.allNodes || this.allNodes.length === 0) {
            return minRadius + ((node.hymn_score || 0) / 1000) * (maxRadius - minRadius);
        }
        
        // Use actual max score from data for better scaling
        const maxScore = Math.max(...this.allNodes.map(n => n.hymn_score));
        const minScore = Math.min(...this.allNodes.map(n => n.hymn_score));
        
        // Scale radius based on hymn score
        const scoreRange = maxScore - minScore;
        if (scoreRange === 0) return minRadius;
        
        const normalizedScore = (node.hymn_score - minScore) / scoreRange;
        return minRadius + (normalizedScore * (maxRadius - minRadius));
    }

    GetNodeColor(node) {
        // Color based on deity count
        const colors = [
            "#ff6b6b", "#4ecdc4", "#45b7d1", "#96ceb4", 
            "#ffeaa7", "#dda0dd", "#98d8c8", "#f7dc6f"
        ];
        return colors[node.deity_count % colors.length] || "#95a5a6";
    }

    async OnNodeClick(nodeId) {
        if (this.pendingRequests.has(nodeId)) return;
        
        this.pendingRequests.add(nodeId);
        d3.select("#loading").style("display", "block").text("Loading similar hymns...");

        try {
            const response = await fetch(`/api/node/${nodeId}?limit=8`);
            const data = await response.json();

            // Arrange neighbors in a ring around clicked node
            const center = this.nodes.get(nodeId);
            const neighbors = data.neighbors;
            const ringRadius = 160;

            neighbors.forEach((nb, i) => {
                const angle = (i / Math.max(1, neighbors.length)) * Math.PI * 2;
                const nx = center.x + Math.cos(angle) * ringRadius;
                const ny = center.y + Math.sin(angle) * ringRadius;

                const existing = this.nodes.get(nb.id);
                const positioned = {
                    ...(existing || nb),
                    x: nx,
                    y: ny,
                    fx: nx,
                    fy: ny
                };
                this.nodes.set(nb.id, positioned);

                const linkId = `${nodeId}-${nb.id}`;
                if (!this.links.has(linkId)) {
                    this.links.set(linkId, { source: nodeId, target: nb.id, similarity: nb.similarity });
                }
            });

            // Fix center node position for focus layout
            center.fx = center.x;
            center.fy = center.y;

            // Update selected node
            this.selectedNode = nodeId;
            this.focusNodeId = nodeId;
            this.focusNeighborIds = new Set(neighbors.map(n => n.id));
            this.isFocusMode = true;
            this.UpdateVisualization();
            this.ShowNodeInfo(data.node);
            this.FocusViewportOnNode(center, 2.2);

        } catch (error) {
            console.error('Error loading node data:', error);
        } finally {
            this.pendingRequests.delete(nodeId);
            d3.select("#loading").style("display", "none");
        }
    }

    UpdateVisualization() {
        const nodesArray = Array.from(this.nodes.values());
        const linksArray = this.showLinks ? Array.from(this.links.values()) : [];
        
        console.log(`UpdateVisualization: ${nodesArray.length} nodes, ${linksArray.length} links`);

        // Update simulation data
        this.simulation.nodes(nodesArray);
        this.simulation.force("link").links(linksArray);

        // Update links (hidden when showLinks is false)
        if (this.showLinks) {
            const linkSelection = this.linkGroup
                .selectAll(".link")
                .data(linksArray, d => `${d.source.id || d.source}-${d.target.id || d.target}`);

            linkSelection.enter()
                .append("line")
                .attr("class", "link")
                .style("stroke-width", d => Math.max(0.5, d.similarity * 2))
                .style("stroke-opacity", d => {
                    if (!this.isFocusMode) return 0.2 + d.similarity * 0.6;
                    const a = d.source.id || d.source;
                    const b = d.target.id || d.target;
                    const inFocus = (a === this.focusNodeId || this.focusNeighborIds.has(a)) &&
                                    (b === this.focusNodeId || this.focusNeighborIds.has(b));
                    return inFocus ? 0.9 : 0.08;
                });

            linkSelection.exit().remove();
        } else {
            this.linkGroup.selectAll(".link").remove();
        }

        // Update nodes
        const nodeSelection = this.nodeGroup
            .selectAll(".node-group")
            .data(nodesArray, d => d.id);

        const nodeEnter = nodeSelection.enter()
            .append("g")
            .attr("class", "node-group");

        nodeEnter
            .append("circle")
            .attr("class", "node")
            .attr("r", d => this.GetNodeRadius(d))
            .attr("fill", d => this.GetNodeColor(d))
            .on("click", (event, d) => {
                event.stopPropagation();
                this.OnNodeClick(d.id);
            })
            .on("mouseover", (event, d) => this.ShowTooltip(event, d))
            .on("mouseout", () => this.HideTooltip())
            .call(d3.drag()
                .on("start", (event, d) => this.DragStarted(event, d))
                .on("drag", (event, d) => this.Dragged(event, d))
                .on("end", (event, d) => this.DragEnded(event, d))
            );

        // Add labels only for top nodes (top 5% by score)
        const topNodes = [...nodesArray].sort((a, b) => b.hymn_score - a.hymn_score).slice(0, Math.ceil(nodesArray.length * 0.05));
        const topNodeIds = new Set(topNodes.map(n => n.id));

        nodeEnter
            .append("text")
            .attr("class", "node-label")
            .attr("dy", ".35em")
            .style("font-size", d => {
                if (topNodeIds.has(d.id)) {
                    return Math.max(8, this.GetNodeRadius(d) / 2) + "px";
                }
                return "0px";
            })
            .style("opacity", d => topNodeIds.has(d.id) ? 1 : 0)
            .text(d => topNodeIds.has(d.id) ? d.hymn_number : "");

        // Update existing nodes
        nodeSelection
            .style("opacity", d => {
                if (!this.isFocusMode) return 1;
                return (d.id === this.focusNodeId || this.focusNeighborIds.has(d.id)) ? 1 : 0.15;
            });

        nodeSelection.select(".node")
            .classed("selected", d => d.id === this.selectedNode)
            .attr("r", d => this.GetNodeRadius(d));

        nodeSelection.select(".node-label")
            .style("font-size", d => {
                if (topNodeIds.has(d.id)) {
                    return Math.max(8, this.GetNodeRadius(d) / 2) + "px";
                }
                return "0px";
            })
            .style("opacity", d => topNodeIds.has(d.id) ? 1 : 0)
            .text(d => topNodeIds.has(d.id) ? d.hymn_number : "");

        nodeSelection.exit().remove();

        // Update simulation
        this.simulation.on("tick", () => {
            if (this.showLinks) {
                this.linkGroup.selectAll(".link")
                    .attr("x1", d => d.source.x)
                    .attr("y1", d => d.source.y)
                    .attr("x2", d => d.target.x)
                    .attr("y2", d => d.target.y);
            }

            this.nodeGroup.selectAll(".node-group")
                .attr("transform", d => `translate(${d.x},${d.y})`);
        });

        console.log(`Starting simulation with ${nodesArray.length} nodes`);
        this.simulation.alpha(0.1).restart();
    }

    ClearFocusMode() {
        if (!this.isFocusMode) return;
        const center = this.nodes.get(this.focusNodeId);
        if (center) { center.fx = null; center.fy = null; }
        this.focusNeighborIds.forEach(id => {
            const n = this.nodes.get(id);
            if (n) { n.fx = null; n.fy = null; }
        });
        this.isFocusMode = false;
        this.focusNodeId = null;
        this.focusNeighborIds = new Set();
        this.selectedNode = null;
        this.HideInfoPanel();
        this.UpdateVisualization();
    }

    ShowTooltip(event, node) {
        this.tooltip
            .style("display", "block")
            .html(`
                <strong>${node.title}</strong><br/>
                Book ${node.book_number}, Hymn ${node.hymn_number}<br/>
                Score: ${node.hymn_score.toFixed(1)}<br/>
                Deities: ${node.deity_count}<br/>
                <em>${node.deity_names}</em>
            `)
            .style("left", (event.pageX + 10) + "px")
            .style("top", (event.pageY - 10) + "px");
    }

    HideTooltip() {
        this.tooltip.style("display", "none");
    }

    ShowNodeInfo(node) {
        d3.select("#info").style("display", "block");
        d3.select("#infoTitle").text(node.title);
        d3.select("#infoBook").text(node.book_number);
        d3.select("#infoHymn").text(node.hymn_number);
        d3.select("#infoScore").text(node.hymn_score.toFixed(1));
        d3.select("#infoDeities").text(node.deity_names || "Unknown");
        d3.select("#infoDeityCount").text(node.deity_count);
    }

    HideInfoPanel() {
        d3.select("#info").style("display", "none");
    }

    DragStarted(event, d) {
        if (!event.active) this.simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
    }

    Dragged(event, d) {
        d.fx = event.x;
        d.fy = event.y;
    }

    DragEnded(event, d) {
        if (!event.active) this.simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
    }

    ResetView() {
        this.svg.transition().duration(750).call(
            this.zoom.transform,
            d3.zoomIdentity
        );
    }

    CenterGraph() {
        const nodes = Array.from(this.nodes.values());
        if (nodes.length === 0) return;

        const bounds = {
            x: d3.extent(nodes, d => d.x),
            y: d3.extent(nodes, d => d.y)
        };

        const dx = bounds.x[1] - bounds.x[0];
        const dy = bounds.y[1] - bounds.y[0];
        const x = (bounds.x[0] + bounds.x[1]) / 2;
        const y = (bounds.y[0] + bounds.y[1]) / 2;
        
        const rawScale = Math.min(this.width / dx, this.height / dy) * 0.6;
        const scale = Number.isFinite(rawScale) ? Math.max(1, Math.min(rawScale, 3)) : 1;
        const translate = [this.width / 2 - scale * x, this.height / 2 - scale * y];

        this.svg.transition().duration(750).call(
            this.zoom.transform,
            d3.zoomIdentity.translate(translate[0], translate[1]).scale(scale)
        );
    }

    async FocusOnNode(hymnId) {
        // Add node to graph if not already present
        if (!this.nodes.has(hymnId)) {
            const foundNode = this.allNodes.find(node => node.id === hymnId);
            if (foundNode) {
                this.nodes.set(hymnId, { 
                    ...foundNode, 
                    x: this.width / 2, 
                    y: this.height / 2 
                });
                this.UpdateVisualization();
            }
        }

        // Load neighbors and focus on the node
        await this.OnNodeClick(hymnId);
        
        // Center the view on this node
        const node = this.nodes.get(hymnId);
        if (node) {
            const scale = 1.5;
            const translate = [
                this.width / 2 - scale * node.x,
                this.height / 2 - scale * node.y
            ];

            this.svg.transition().duration(750).call(
                this.zoom.transform,
                d3.zoomIdentity.translate(translate[0], translate[1]).scale(scale)
            );
        }
    }
}

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM loaded, initializing Hymn Similarity Map...');
    new HymnSimilarityMap();
});