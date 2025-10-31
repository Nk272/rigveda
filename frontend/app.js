class HymnSimilarityMap 
{
    constructor()
    {
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

        // Load deity count from localStorage or default to 4
        const savedDeityCount = localStorage.getItem('rigveda_deity_count');
        this.currentDeityCount = savedDeityCount ? parseInt(savedDeityCount) : 4;

        this.hymnTexts = {}; // Cache for hymn texts

        this.InitializeSvg();
        this.InitializeSimulation();
        this.InitializeTooltip();
        this.InitializeControls();
        this.LoadInitialData();
    }

    InitializeSvg() 
    {
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
        const maxRadius = Math.min(this.width, this.height) * 0.43;

        this.simulation = d3.forceSimulation()
            .force("link", d3.forceLink()
                .id(d => d.id)
                .distance(d => 30 + (1 - (d.similarity || 0)) * 80)
                .strength(d => (d.similarity || 0) * 0.3)
            )
            .force("charge", d3.forceManyBody()
                .strength(-2.0)
                .distanceMax(60)
            )
            .force("center", d3.forceCenter(this.width / 2, this.height / 2).strength(0.02))
            .force("collision", d3.forceCollide()
                .radius(d => this.GetNodeRadius(d) + 2.5)
                .strength(0.95)
                .iterations(5)
            )
            // Keep nodes inside the circle without pulling them to the rim
            .force("boundary", this.CreateCircularBoundaryForce(maxRadius))
            .alphaDecay(0.018)
            .velocityDecay(0.65);
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
        d3.select("#centerBtn").on("click", () => this.CenterGraph());

        // Hard reload button
        d3.select("#hardReloadBtn").on("click", () => {
            // Clear localStorage and reload
            localStorage.removeItem('rigveda_deity_count');
            location.reload(true);
        });

        // Handle deity count slider
        const slider = d3.select("#deityCountSlider");
        const input = d3.select("#deityCountInput");
        const valueDisplay = d3.select("#deityCountValue");

        // Set initial value from loaded deity count
        slider.property("value", this.currentDeityCount);
        if (!input.empty()) input.property("value", this.currentDeityCount);
        valueDisplay.text(this.currentDeityCount);

        const minVal = parseInt(slider.attr("min"));
        const maxVal = parseInt(slider.attr("max"));

        slider.on("input", (event) => {
            let value = parseInt(event.target.value, 10);
            if (!Number.isFinite(value)) value = this.currentDeityCount;
            value = Math.max(minVal, Math.min(maxVal, value));
            valueDisplay.text(value);
            if (!input.empty()) input.property("value", value);
        });

        slider.on("change", (event) => {
            let value = parseInt(event.target.value, 10);
            if (!Number.isFinite(value)) value = this.currentDeityCount;
            value = Math.max(minVal, Math.min(maxVal, value));

            // Save to localStorage
            localStorage.setItem('rigveda_deity_count', value);

            // Reload the page to apply changes
            location.reload();
        });

        if (!input.empty()) {
            input.on("input", (event) => {
                const raw = event.target.value;
                let value = parseInt(raw, 10);
                if (!Number.isFinite(value)) {
                    // Revert to last known good without committing
                    event.target.value = this.currentDeityCount;
                    return;
                }
                value = Math.max(minVal, Math.min(maxVal, value));
                event.target.value = value;
                slider.property("value", value);
                valueDisplay.text(value);
            });

            input.on("change", (event) => {
                let value = parseInt(event.target.value, 10);
                if (!Number.isFinite(value)) value = this.currentDeityCount;
                value = Math.max(minVal, Math.min(maxVal, value));
                event.target.value = value;
                localStorage.setItem('rigveda_deity_count', value);
                location.reload();
            });
        }

        // Handle backdrop click to close info panel
        d3.select("#backdrop").on("click", () => this.CloseInfoPanel());

        // Handle window resize
        window.addEventListener("resize", () => {
            this.width = window.innerWidth;
            this.height = window.innerHeight;
            this.svg.attr("width", this.width).attr("height", this.height);
            // this.simulation.force("center", d3.forceCenter(this.width / 2, this.height / 2));
            this.simulation.alpha(0.3).restart();
        });
    }

    async LoadInitialData() {
        try {
            console.log(`Loading data for top ${this.currentDeityCount} deities...`);
            d3.select("#loading").text(`Loading hymns for top ${this.currentDeityCount} deities...`);

            // Clear existing nodes
            this.nodes.clear();
            this.links.clear();

            // Load nodes filtered by deity count
            const response = await fetch(`/api/graph/by-deities?n=${this.currentDeityCount}`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            console.log(`Loaded ${data.nodes.length} nodes for ${this.currentDeityCount} deities`);

            this.allNodes = data.nodes;

            // Update completion tracker
            this.UpdateCompletionTracker(data.nodes.length);

            // Position nodes by deity clustering
            this.PositionNodesByDeity(data.nodes);

            // Add all nodes to the map
            data.nodes.forEach(node => {
                this.nodes.set(node.id, node);
            });

            console.log(`Added ${this.nodes.size} nodes to visualization`);
            this.UpdateVisualizationStatic();

            d3.select("#loading").style("display", "none");
        } catch (error) {
            console.error('Error loading initial data:', error);
            d3.select("#loading").text(`Error: ${error.message}`);
        }
    }

    UpdateCompletionTracker(displayedCount) {
        const totalHymns = 1028;
        const percentage = (displayedCount / totalHymns) * 100;

        d3.select("#hymnCount").text(displayedCount);
        d3.select("#hymnPercent").text(percentage.toFixed(1));
        d3.select("#progressFill").style("width", `${percentage}%`);
    }

    CreateClusterForce() {
        const strength = 0.2;
        return alpha => {
            const centroids = this.CalculateDeityCentroids();
            this.allNodes.forEach(node => {
                if (node.primary_deity_id !== null && centroids[node.primary_deity_id]) {
                    const centroid = centroids[node.primary_deity_id];
                    node.vx -= (node.x - centroid.x) * strength * alpha;
                    node.vy -= (node.y - centroid.y) * strength * alpha;
                }
            });
        };
    }

    CalculateDeityCentroids() {
        // Group nodes by deity
        const deityGroups = {};
        this.allNodes.forEach(node => {
            if (node.primary_deity_id !== null) {
                if (!deityGroups[node.primary_deity_id]) {
                    deityGroups[node.primary_deity_id] = [];
                }
                deityGroups[node.primary_deity_id].push(node);
            }
        });

        // Calculate centroid positions in a single circular arrangement
        const centerX = this.width / 2;
        const centerY = this.height / 2;
        const centroids = {};

        // Sort deities by hymn count (descending)
        const deityIds = Object.keys(deityGroups).map(Number);
        const deityCounts = deityIds.map(id => ({
            id,
            count: deityGroups[id].length
        })).sort((a, b) => b.count - a.count);

        const totalDeities = deityCounts.length;

        // Calculate radius based on screen size - match the simulation maxRadius
        const maxRadius = Math.min(this.width, this.height) * 0.43;

        // Arrange deity clusters uniformly in a circular pattern
        deityCounts.forEach((deity, index) => {
            const angle = (index / totalDeities) * 2 * Math.PI - Math.PI / 2; // Start from top

            // Use uniform radius for all deities to maintain circular boundary
            const radiusFactor = 0.6; // Single uniform factor for cluster centers
            const radius = maxRadius * radiusFactor;

            centroids[deity.id] = {
                x: centerX + Math.cos(angle) * radius,
                y: centerY + Math.sin(angle) * radius
            };
        });

        return centroids;
    }

    CreateCircularBoundaryForce(maxRadius) {
        const stiffness = 0.4;
        return (alpha) => {
            const cx = this.width / 2;
            const cy = this.height / 2;
            const nodes = this.simulation.nodes();
            for (let i = 0; i < nodes.length; i++) {
                const n = nodes[i];
                const dx = n.x - cx;
                const dy = n.y - cy;
                const dist = Math.hypot(dx, dy) || 1;
                const allowed = maxRadius - (this.GetNodeRadius(n) + 1);
                if (dist > allowed) {
                    const s = allowed / dist;
                    const tx = cx + dx * s;
                    const ty = cy + dy * s;
                    n.vx += (tx - n.x) * stiffness * alpha;
                    n.vy += (ty - n.y) * stiffness * alpha;
                }
            }
        };
    }

    PositionNodesByDeity(nodes) {
        console.log(`Positioning ${nodes.length} nodes uniformly in circle with sector clustering`);

        const cx = this.width / 2;
        const cy = this.height / 2;
        const maxRadius = Math.min(this.width, this.height) * 0.43;
        const margin = 8; // keep nodes away from the edge slightly

        // Group nodes by deity
        const deityGroups = {};
        nodes.forEach(node => {
            if (!deityGroups[node.primary_deity_id]) deityGroups[node.primary_deity_id] = [];
            deityGroups[node.primary_deity_id].push(node);
        });

        // Sort deities by size, then separate similar colors
        const deityIds = Object.keys(deityGroups).map(Number);
        const deityCounts = deityIds.map(id => ({
            id,
            count: deityGroups[id].length,
            color: deityGroups[id][0].deity_color
        })).sort((a, b) => b.count - a.count);

        const arrangedDeities = this.ArrangeDeitiesWithColorSeparation(deityCounts);

        // Assign angular sectors proportional to group sizes
        const totalNodes = nodes.length;
        const gap = Math.min(0.08, 2 * Math.PI * 0.01); // small gap between sectors
        let angleCursor = -Math.PI / 2; // start at top

        const sectors = arrangedDeities.map(d => {
            const span = Math.max(0.3, (d.count / totalNodes) * (2 * Math.PI - arrangedDeities.length * gap));
            const start = angleCursor;
            const end = start + span;
            angleCursor = end + gap;
            return { deityId: d.id, start, end };
        });

        // Place nodes uniformly inside their sector (blue-noise like start)
        sectors.forEach(sec => {
            const group = deityGroups[sec.deityId];
            for (let i = 0; i < group.length; i++) {
                const node = group[i];
                const angle = sec.start + Math.random() * (sec.end - sec.start);
                const r = (Math.sqrt(Math.random()) * (maxRadius - margin));
                node.x = cx + Math.cos(angle) * r;
                node.y = cy + Math.sin(angle) * r;
                node.vx = 0; node.vy = 0;
            }
        });

        console.log(`Placed ${nodes.length} nodes with sector-based uniform distribution`);
    }

    ArrangeDeitiesWithColorSeparation(deityCounts) {
        // Use a greedy approach to separate similar colors
        if (deityCounts.length <= 1) return deityCounts;

        const arranged = [deityCounts[0]];
        const remaining = deityCounts.slice(1);

        while (remaining.length > 0) {
            const lastColor = arranged[arranged.length - 1].color;

            // Find the deity with most different color from the last one
            let maxDiff = -1;
            let maxDiffIndex = 0;

            remaining.forEach((deity, index) => {
                const diff = this.ColorDifference(lastColor, deity.color);
                if (diff > maxDiff) {
                    maxDiff = diff;
                    maxDiffIndex = index;
                }
            });

            arranged.push(remaining[maxDiffIndex]);
            remaining.splice(maxDiffIndex, 1);
        }

        return arranged;
    }

    ColorDifference(color1, color2) {
        // Simple RGB distance calculation
        const rgb1 = this.HexToRgb(color1);
        const rgb2 = this.HexToRgb(color2);

        if (!rgb1 || !rgb2) return 0;

        return Math.sqrt(
            Math.pow(rgb1.r - rgb2.r, 2) +
            Math.pow(rgb1.g - rgb2.g, 2) +
            Math.pow(rgb1.b - rgb2.b, 2)
        );
    }

    HexToRgb(hex) {
        const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
        return result ? {
            r: parseInt(result[1], 16),
            g: parseInt(result[2], 16),
            b: parseInt(result[3], 16)
        } : null;
    }

    PositionNodesByScore(nodes) {
        console.log(`Positioning ${nodes.length} nodes in circular pattern`);

        const centerX = this.width / 2;
        const centerY = this.height / 2;

        // Calculate base radius for the circle - match the simulation maxRadius
        const baseRadius = Math.min(this.width, this.height) * 0.43;

        // Sort nodes by score to position high-scoring nodes closer to center
        const sortedNodes = [...nodes].sort((a, b) => b.hymn_score - a.hymn_score);

        // Calculate appropriate spacing based on node sizes
        const avgNodeRadius = 8; // Average node radius including stroke
        const minSpacing = avgNodeRadius * 2.5; // Minimum distance between node centers

        let placedNodes = 0;
        let ringIndex = 0;

        while (placedNodes < sortedNodes.length) {
            // Calculate radius for this ring
            const ringRadius = ringIndex === 0 ? 0 : baseRadius * 0.2 + (ringIndex * minSpacing);

            // Calculate how many nodes can fit in this ring based on circumference
            let nodesInThisRing;
            if (ringIndex === 0) {
                nodesInThisRing = 1; // Single node at center
            } else {
                const circumference = 2 * Math.PI * ringRadius;
                nodesInThisRing = Math.floor(circumference / minSpacing);
                nodesInThisRing = Math.max(6, nodesInThisRing); // Minimum 6 nodes per ring
            }

            // Limit nodes in this ring to remaining nodes
            nodesInThisRing = Math.min(nodesInThisRing, sortedNodes.length - placedNodes);

            // Place nodes in this ring
            for (let i = 0; i < nodesInThisRing; i++) {
                const node = sortedNodes[placedNodes];

                // Calculate angle - evenly distribute nodes around the ring
                const angle = (i / nodesInThisRing) * 2 * Math.PI;

                node.x = centerX + Math.cos(angle) * ringRadius;
                node.y = centerY + Math.sin(angle) * ringRadius;
                node.vx = 0;
                node.vy = 0;

                placedNodes++;
            }

            ringIndex++;
        }

        console.log(`Placed ${placedNodes} nodes in ${ringIndex} concentric rings`);
    }

    GetNodeRadius(node) {
        const minRadius = 4;
        const maxRadius = 20;

        // Use word_count for node size
        // Fallback if allNodes is not loaded yet
        if (!this.allNodes || this.allNodes.length === 0) {
            const wordCount = node.word_count || 100;
            return minRadius + Math.min((wordCount / 500) * (maxRadius - minRadius), maxRadius - minRadius);
        }

        // Use actual max/min word count from data for better scaling
        const maxWordCount = Math.max(...this.allNodes.map(n => n.word_count || 0));
        const minWordCount = Math.min(...this.allNodes.map(n => n.word_count || 0));

        // Scale radius based on word count
        const wordCountRange = maxWordCount - minWordCount;
        if (wordCountRange === 0) return minRadius;

        const normalizedWordCount = ((node.word_count || 0) - minWordCount) / wordCountRange;
        return minRadius + (normalizedWordCount * (maxRadius - minRadius));
    }

    GetNodeColor(node) {
        // Use deity color from API
        return node.deity_color || "#95a5a6";
    }

    GetHindiTranslationUrl(bookNumber, hymnNumber) {
        const hymnStr = String(hymnNumber).padStart(3, '0');
        const prefix = Number(bookNumber) === 10 ? '' : `0f`;
        return `https://sacred-texts.com/hin/rvsan/rv${prefix}${hymnStr}.htm`;
    }

	OpenHindiOriginal(bookNumber, hymnNumber) {
		const url = this.GetHindiTranslationUrl(bookNumber, hymnNumber);
		window.open(url, '_blank', 'noopener');
	}

    async ToggleEnglishTranslation(bookNumber, nodeId) {
        const containerId = `english-trans-${nodeId}`;
        const buttonId = `english-btn-${nodeId}`;
        const container = document.getElementById(containerId);
        const button = document.getElementById(buttonId);
        if (!container || !button) return;

        const isVisible = container.style.display !== 'none' && container.style.display !== '';
        if (isVisible) {
            container.style.display = 'none';
            button.textContent = 'Show English Translation';
            return;
        }

        // Load once if not loaded
        if (!container.dataset.loaded) {
            try {
                const hymnPath = `/Data/rigveda_texts/book_${bookNumber}/hymn_${nodeId}.txt`;
                const textResponse = await fetch(hymnPath);
                if (textResponse.ok) {
                    const fullText = await textResponse.text();
                    const parts = fullText.split('==================================================');
                    const hymnText = (parts.length > 1 ? parts[1] : fullText).trim();
                    container.innerHTML = hymnText;
                } else {
                    container.textContent = 'Translation not available.';
                }
            } catch (error) {
                console.error('Error loading hymn text:', error);
                container.textContent = 'Translation not available.';
            }
            container.dataset.loaded = 'true';
        }

        container.style.display = 'block';
        button.textContent = 'Hide English Translation';
    }

    async OnNodeClick(nodeId) {
        if (this.pendingRequests.has(nodeId)) return;

        this.pendingRequests.add(nodeId);
        d3.select("#loading").style("display", "block").text("Loading hymn details...");

        try {
            const response = await fetch(`/api/node/${nodeId}?limit=4`);
            const data = await response.json();

            // Update selected node
            this.selectedNode = nodeId;
            this.focusNodeId = nodeId;
            this.focusNeighborIds = new Set(data.neighbors.map(n => n.id));
            this.isFocusMode = false; // Don't fade other nodes
            this.UpdateVisualization();

            // Show hymn info with summary and similar hymns
            this.ShowNodeInfoWithSummary(data.node, data.neighbors, nodeId);

            // Focus viewport on node
            const center = this.nodes.get(nodeId);
            if (center) {
                this.FocusViewportOnNode(center, 2);
            }

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
        this.simulation.alpha(0.05).restart();
    }

    UpdateVisualizationStatic() {
        const nodesArray = Array.from(this.nodes.values());
        const linksArray = this.showLinks ? Array.from(this.links.values()) : [];

        console.log(`UpdateVisualizationStatic: ${nodesArray.length} nodes, ${linksArray.length} links`);

        // Update simulation data
        this.simulation.nodes(nodesArray);
        this.simulation.force("link").links(linksArray);

        // Pre-compute collision resolution before showing nodes
        console.log('Pre-computing collision resolution...');
        d3.select("#loading").text("Optimizing layout...");

        // Run simulation in background without updating DOM
        const targetAlpha = 0.001; // Threshold for stable simulation
        const maxIterations = 300; // Safety limit
        let iterations = 0;

        this.simulation.on("tick", null); // Temporarily disable tick updates

        // Run simulation until it stabilizes
        while (this.simulation.alpha() > targetAlpha && iterations < maxIterations) {
            this.simulation.tick();
            iterations++;
        }

        console.log(`Completed ${iterations} pre-computation iterations (alpha: ${this.simulation.alpha().toFixed(4)})`);

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

        // Now set positions to the pre-computed stable positions
        if (this.showLinks) {
            this.linkGroup.selectAll(".link")
                .attr("x1", d => d.source.x)
                .attr("y1", d => d.source.y)
                .attr("x2", d => d.target.x)
                .attr("y2", d => d.target.y);
        }

        this.nodeGroup.selectAll(".node-group")
            .attr("transform", d => `translate(${d.x},${d.y})`);

        // Set up tick function for any future dynamic updates (drag, etc.)
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

        // Stop the simulation - nodes are already in stable positions
        this.simulation.stop();
        console.log('Layout optimized and ready for display');
    }

    ClearFocusMode() {
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

    CloseInfoPanel() {
        this.selectedNode = null;
        this.focusNodeId = null;
        this.focusNeighborIds = new Set();
        this.isFocusMode = false;
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

    async ShowNodeInfoWithSummary(node, neighbors, nodeId) {
        const infoPanel = d3.select("#info");
        const backdrop = d3.select("#backdrop");

        infoPanel.style("display", "block");
        backdrop.style("display", "block");

        // Fetch summary for the main hymn
        let summary = "Loading summary...";
        try {
            const summaryResponse = await fetch('/Data/JSONMaps/rigveda_summaries.json');
            const summaries = await summaryResponse.json();
            summary = summaries[nodeId] || "Summary not available.";
        } catch (error) {
            console.error('Error loading summary:', error);
            summary = "Summary not available.";
        }

		// English translation will be loaded on demand via button

        // Build similar hymns HTML with new styling - more compact
        const similarHymnsHtml = neighbors.map((nb, idx) => `
            <div class="similar-hymn" onclick="window.hymnMap.OnNodeClick('${nb.id}')" style="border-left-color: ${nb.deity_color}; padding: 8px 12px; margin: 6px 0;">
                <strong style="color: #5d3a1a; font-size: 14px;">${idx + 1}. ${nb.title}</strong>
                <small style="color: #6d5638; font-weight: 600; display: block; margin-top: 2px;">
                    Book ${nb.book_number}.${nb.hymn_number} • ${(nb.similarity * 100).toFixed(1)}%
                    &nbsp;·&nbsp;
                    <a href="${this.GetHindiTranslationUrl(nb.book_number, nb.hymn_number)}" target="_blank" rel="noopener noreferrer" style="color: #5d3a1a; text-decoration: underline;">हिन्दी</a>
                </small>
            </div>
        `).join('');

        infoPanel.html(`
            <div style="display: flex; flex-direction: column; gap: 15px;">
                <h3 style="color: ${node.deity_color}; border-bottom-color: ${node.deity_color}; margin: 0;">
                    ${node.title}
                </h3>

                <div style="display: flex; gap: 20px; flex-wrap: wrap;">
                    <div style="flex: 1; min-width: 300px;">
                        <!-- General Hymn Info -->
                        <div style="padding: 12px; background: rgba(139, 111, 71, 0.08); border-radius: 6px; border: 2px solid rgba(139, 111, 71, 0.2); margin-bottom: 12px;">
                            <h4 style="margin: 0 0 8px 0; color: #5d3a1a; font-size: 16px;">Hymn Information</h4>
                            <p style="margin: 5px 0; font-size: 14px;">
                                <strong>Book:</strong> ${node.book_number} &nbsp;|&nbsp; <strong>Hymn Number:</strong> ${node.hymn_number}
                            </p>
                            <p style="margin: 5px 0; font-size: 14px;">
                                <strong>Assigned Deity:</strong> <span style="color: ${node.deity_color}; font-weight: 700;">${node.deity_names || "Unknown"}</span>
                            </p>
                            <p style="margin: 5px 0; font-size: 14px;">
                                <strong>Title:</strong> ${node.title}
                            </p>
                        </div>

						<!-- Summary -->
                        <div class="summary-section" style="border-left-color: ${node.deity_color}; margin: 0 0 12px 0; padding: 12px;">
                            <h4 style="margin: 0 0 8px 0;">सारांश (Summary)</h4>
                            <p style="font-size: 13px; line-height: 1.6; margin: 0;">
                                ${summary}
                            </p>
                        </div>

						<!-- Original Hymn Text (Hindi/Sanskrit) -->
						<div class="summary-section" style="border-left-color: ${node.deity_color}; margin: 0; padding: 12px;">
							<h4 style="margin: 0 0 8px 0;">मूल सूक्त (Original Hymn Text)</h4>
							<button onclick="window.hymnMap.OpenHindiOriginal(${node.book_number}, ${node.hymn_number})" style="width: auto; padding: 6px 12px;">
								Open Original Hymn Text
							</button>
						</div>

						<!-- English Translation (on demand) -->
						<div class="summary-section" style="border-left-color: ${node.deity_color}; margin: 12px 0 0 0; padding: 12px;">
							<h4 style="margin: 0 0 8px 0;">English Translation</h4>
							<button id="english-btn-${nodeId}" onclick="window.hymnMap.ToggleEnglishTranslation(${node.book_number}, '${nodeId}')" style="width: auto; padding: 6px 12px; margin-bottom: 8px;">
								Show English Translation
							</button>
							<div id="english-trans-${nodeId}" data-loaded="" style="display: none; font-size: 13px; line-height: 1.7; margin: 0; max-height: 300px; overflow-y: auto;"></div>
						</div>
                    </div>

                    <div style="flex: 0 0 280px; min-width: 280px;">
                        <h4 style="margin: 0 0 10px 0; color: #5d3a1a; font-size: 16px; text-align: center; font-family: 'Noto Serif Devanagari', serif;">
                            समान सूक्त (Similar Hymns)
                        </h4>
                        ${similarHymnsHtml}
                    </div>
                </div>

                <button onclick="window.hymnMap.CloseInfoPanel()" style="align-self: center; width: auto; padding: 10px 40px;">
                    Close
                </button>
            </div>
        `);
    }

    HideInfoPanel() {
        d3.select("#info").style("display", "none");
        d3.select("#backdrop").style("display", "none");
    }

    DragStarted(event, d) {
        // if (!event.active) this.simulation.alphaTarget(0.3).restart();
        // d.fx = d.x;
        // d.fy = d.y;
    }

    Dragged(event, d) {
        // d.fx = event.x;
        // d.fy = event.y;
    }

    DragEnded(event, d) {
        // if (!event.active) this.simulation.alphaTarget(0);
        // d.fx = null;
        // d.fy = null;
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

    
}

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM loaded, initializing Hymn Similarity Map...');
    window.hymnMap = new HymnSimilarityMap();
});