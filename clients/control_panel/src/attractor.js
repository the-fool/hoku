function AttractorWidget(canvasContainer, controlsContainer, fxWs) {
    // Input: a container jquery elm
    const self = this;

    self.presets = [{
        "species": "DEFAULT",
        "A": 0.3,
        "B": 0.8,
        "C": 1.9,
        "D": 2.8,
        "E": 2.3
    }];

    var canvas,
        gl = null,
        pointSize = 1.0,
        running = true,
        dragging = false,
        mouseX = 0,
        mouseY = 0,
        rotAccX = 0,
        rotAccY = 0,
        x, y, z,
        rotx = 0,
        roty = 0,
        rotz = 0,
        vbuffer,
        program,
        fshaderCode =
        "#ifdef GL_ES\n" +
        "precision mediump float;\n" +
        "#endif\n" +
        "varying vec3 vPosition;\n" +
        "void main(void) {\n" +
        "	float r = 0.3 + 0.7 * vPosition.x;\n" +
        "	float g = 0.3 + 0.7 * vPosition.y;\n" +
        "	float b = 0.7 + 0.3 * vPosition.z;\n" +
        "	gl_FragColor = vec4(r, g, b, 0.65);\n" +
        "}",
        vshaderCode =
        "attribute vec3 ppos;\n" +
        "varying vec3 vPosition;\n" +
        "uniform mat4 uMVMatrix;\n" +
        "uniform mat4 uPMatrix;\n" +
        "attribute float a_pointSize;\n" +
        "void main(void) {\n" +
        "	gl_PointSize = a_pointSize;" +
        "	gl_Position = uPMatrix * uMVMatrix * vec4(ppos.x, ppos.y, ppos.z, 1.0);\n" +
        "	vPosition = ppos;\n" +
        "}",
        gui,
        attractor;

    function toRad(deg) {
        return deg * Math.PI / 180;
    }

    function getRotationMatrix(rx, ry, rz) {
        var cx = Math.cos(rx),
            sx = Math.sin(rx),
            cy = Math.cos(ry),
            sy = Math.sin(ry),
            cz = Math.cos(rz),
            sz = Math.sin(rz);

        return new Float32Array([
            cy * cz, sx * sy * cz - cx * sz, sx * sz + cx * sy * cz, 0,
            cy * sz, sx * sy * sz + cx * cz, cx * sy * sz - sx * cz, 0, -sy, sx * cy, cx * cy, 0,
            0, 0, 0, 1
        ]);
    }

    function draw() {
        if (!running || !gl) return;

        window.requestAnimationFrame(draw);

        // gl.viewport(0, 0, gl.viewportWidth, gl.viewportHeight);
        var size = Math.min(gl.viewportWidth, gl.viewportHeight);
        gl.viewport(0, 0, size, size);

        gl.clearColor(0.0, 0.0, 0.0, 1.0);
        //gl.clear(gl.COLOR_BUFFER_BIT);
        gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);

        //rotAccX *= 0.75;
        //rotAccY *= 0.75;
        //rotx = Math.max(Math.min(rotx + 0.5 * rotAccX, 90), -90);

        rotx = rotx + 0.5 * rotAccX % 360;
        roty = roty + 0.5 * rotAccY % 360;
        //rotz = (rotz) % 360;

        //setMatrixUniforms();
        var mvUniform = gl.getUniformLocation(program, 'uMVMatrix');
        if (mvUniform == -1) {
            console.error('Error during uniform address retrieval: "uMVMatrix"');
            running = false;
            return;
        }
        var mvMatrix = getRotationMatrix(toRad(rotx), toRad(roty), toRad(rotz));
        /*var mvMatrix = mat4.create();
          mat4.rotate(mvMatrix, toRad(rotx), [1, 0, 0], mvMatrix);
          mat4.rotate(mvMatrix, toRad(roty), [0, 1, 0], mvMatrix);
          mat4.rotate(mvMatrix, toRad(rotz), [0, 0, 1], mvMatrix);*/
        gl.uniformMatrix4fv(mvUniform, false, mvMatrix);

        var pUniform = gl.getUniformLocation(program, 'uPMatrix');
        if (pUniform == -1) {
            console.error('Error during uniform address retrieval: "uPMatrix"');
            running = false;
            return;
        }
        var pMatrix = mat4.create();
        mat4.identity(pMatrix);
        // mat4.perspective(120, gl.viewportWidth / gl.viewportHeight, 0.1, 100.0, pMatrix);
        gl.uniformMatrix4fv(pUniform, false, pMatrix);

        var a_pointSize = gl.getAttribLocation(program, "a_pointSize");
        gl.vertexAttrib1f(a_pointSize, pointSize);

        gl.drawArrays(gl.POINTS, 0, attractor.pointCount);
        gl.flush();
    }

    function initBuffers() {
        console.log('Initializing Buffers...');
        var vattrib = gl.getAttribLocation(program, 'ppos');
        if (vattrib == -1) {
            console.error('Error during attribute address retrieval');
            return;
        }
        gl.enableVertexAttribArray(vattrib);

        vbuffer = gl.createBuffer();
        gl.bindBuffer(gl.ARRAY_BUFFER, vbuffer);

        //var vertices = new Float32Array([0.0, 0.5, -0.5, -0.5, 0.5, -0.5]);
        var vertices = new Float32Array(attractor.points);
        gl.bufferData(gl.ARRAY_BUFFER, vertices, gl.DYNAMIC_DRAW);
        gl.vertexAttribPointer(vattrib, 3, gl.FLOAT, false, 0, 0);
    }

    function initShaders() {
        console.log('Initializing Shaders...');
        var fshader = gl.createShader(gl.FRAGMENT_SHADER);
        gl.shaderSource(fshader, fshaderCode);
        gl.compileShader(fshader);
        if (!gl.getShaderParameter(fshader, gl.COMPILE_STATUS)) {
            console.error('Error during fragment shader compilation:\n' + gl.getShaderInfoLog(fshader));
            return;
        }
        var vshader = gl.createShader(gl.VERTEX_SHADER);
        gl.shaderSource(vshader, vshaderCode);
        gl.compileShader(vshader);
        if (!gl.getShaderParameter(vshader, gl.COMPILE_STATUS)) {
            console.error('Error during vertex shader compilation:\n' + gl.getShaderInfoLog(vshader));
            return;
        }

        program = gl.createProgram();
        gl.attachShader(program, vshader);
        gl.attachShader(program, fshader);
        gl.linkProgram(program);

        if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
            console.error('Error during program linking:\n' + gl.getProgramInfoLog(program));
            return;
        }

        gl.validateProgram(program);
        if (!gl.getProgramParameter(program, gl.VALIDATE_STATUS)) {
            console.error('Error during program validation:\n' + gl.getProgramInfoLog(program));
            return;
        }

        gl.useProgram(program);

        initBuffers();
    }

    function initWebGL() {
        console.log('Initializing WebGL...');
        try {
            gl = canvas.getContext('webgl');
        } catch (e) {
            console.error('Failed to initialize WebGL:\n' + e);
        }

        if (!gl) {
            alert('Failed to initialize WebGL');
        } else {
            gl.viewportWidth = canvas.width = 200;
            gl.viewportHeight = canvas.height = 200;
            gl.blendFunc(gl.SRC_ALPHA, gl.ONE);
            gl.enable(gl.BLEND);

            initShaders();

            draw();
        }
        window.addEventListener('resize', function(e) {
            //gl.viewportWidth = canvas.width = window.innerWidth;
            //gl.viewportHeight = canvas.height = window.innerHeight;
        });
    }

    function addGui() {
      console.log(fxWs);
        function sendWs(msg) {
            fxWs.send(JSON.stringify(msg));
        }
        const pointMax = 40000;
        const pointMin = 100;
        const pointScale = d3.scaleLinear().domain([pointMin, pointMax]).range([0.01, 1]).clamp(true);

      const pointSizeMin = 0.5;
      const pointSizeMax = 9;
      const pointSizeScale = d3.scaleLinear().domain([pointSizeMin, pointSizeMax]).range([0.01, 1]).clamp(true);
        const throttledWsSend = throttle(sendWs, 200);
        gui = new DAT.GUI({
            autoPlace: false
        });

        gui.add(attractor, 'pointCount', 100, 40000, 500).name('Volume').onChange(function(newPointCount) {
            throttledWsSend({
                kind: 'volume',
                payload: pointScale(newPointCount)
            });
            attractor.setPointCount(newPointCount);
        });

        gui.add(attractor, 'pointSize', pointSizeMin, pointSizeMax, 0.01).name('Distortion').onChange(function(x) {

          throttledWsSend({
            kind: 'distortion',
            payload: pointSizeScale(x)
          });
            attractor.setPointSize(x);
        });

        gui.add(attractor, 'blur', 0, 10, 0.01).name('Echo').onChange(attractor.setBlur);
        /*
        gui.add(attractor, 'scale', 0.05, 2.5, 0.05).name('Scale').onChange(function(newScale) {
          attractor.setScale(newScale);
        });
        */
        const min = 0,
            max = 1,
            step = 0.01;


        function addFactorControl(name, key) {
            gui.add(attractor, key, min, max, step).name(name).onChange(function(newValue) {
                attractor.setFactor(key, newValue);
            }).listen();
        }

        const factors = [
            ['Decay', 'D'],
            ['Release', 'A'],
            ['Shape', 'C']
        ];
        factors.forEach(([name, key]) => addFactorControl(name, key));

        controlsContainer.get()[0].appendChild(gui.domElement);
    }

    function initialize() {
        const _canvas = $('<canvas></canvas>');
        canvasContainer.append(_canvas);
        canvas = canvasContainer.find('canvas').get()[0];
        self.attractor = attractor = new Attractor();

        addGui();

        initWebGL(canvas);
        attractor.setSpecies(attractor.DEFAULT);

        function startDrag(e) {
            dragging = true;
            mouseX = e.pageX;
            mouseY = e.pageY;
        }

        function stopDrag(e) {
            if (dragging) {
                dragging = false;
                mouseX = e.pageX;
                mouseY = e.pageY;
            }
        }
        $(canvas).mousedown(startDrag);
        $(canvas).mouseup(stopDrag);
        $(canvas).mouseout(stopDrag);
        $(canvas).mousemove(function(e) {
            if (dragging) {
                rotAccY = (e.pageX - mouseX) % 360;
                rotAccX = (e.pageY - mouseY) % 360;
                mouseX = e.pageX;
                mouseY = e.pageY;
            }
        });
    };

    function Attractor() {
        this.DEFAULT = {
            name: "Default",
            eq: function(me, px, py, pz) {
                x = Math.sin(me._A * py) - pz * Math.cos(me._B * px);
                y = pz * Math.sin(me._C * px) - Math.cos(me._D * py);
                z = me._E * Math.sin(px);
                return [x, y, z];
            }
        };
        this.speciesName = "DEFAULT";
        this.pointSize = pointSize;
        this.species = this.DEFAULT;

        this.factorScale = d3.scaleLinear().domain([0, 1]).range([0.05, 1]);
        // PUBLIC
        this.pointCount = this._pointCount = 7000;
        this.blur = 0;
        this._A = 0.8;
        this._B = .6;
        this._C = 0.6;
        this._D = .5;
        this._E = 1.8;

        this.A = this.factorScale.invert(this._A);
        this.B = this.factorScale.invert(this._B);
        this.C = this.factorScale.invert(this._C);
        this.D = this.factorScale.invert(this._D);

        this.scale = 0.5;
        this.F = 0.0;
        this.G = 0.0;
        this.H = 0.0;
        this.I = 0.0;
        this.create();
        //this.randomize();
        return this;
    }

    Attractor.prototype.randomize = function() {
        var f = Math.pow(10, 1);
        var m = 5 * f;
        this.A = Math.floor(Math.random() * m - f) / f;
        this.B = Math.floor(Math.random() * m - f) / f;
        this.C = Math.floor(Math.random() * m - f) / f;
        this.D = Math.floor(Math.random() * m - f) / f;
        this.E = Math.floor(Math.random() * m - f) / f;
        this.F = Math.floor(Math.random() * m - f) / f;
        this.G = Math.floor(Math.random() * m - f) / f;
        this.H = Math.floor(Math.random() * m - f) / f;
        this.I = Math.floor(Math.random() * m - f) / f;
        this.create();
        initBuffers();
        return this;
    };

    Attractor.prototype.setSpecies = function(ob) {
        this.species = ob;
        this.create();
        initBuffers();
        return this;
    };

    Attractor.prototype.setScale = function(newScale) {
        this.scale = newScale;
        this.create();
        initBuffers();
        return this;
    };

    Attractor.prototype.setFactor = function(f, newValue) {
        this[f] = newValue;
        this[`_${f}`] = this.factorScale(newValue);

        this.create();
        initBuffers();
        return this;
    };

    Attractor.prototype.setPointCount = function(n) {
        var p, lp;
        if (n > this._pointCount) {
            this.pointCount = this._pointCount = n;
            /*while (this.points.length/3 < n) {
     // Use last point in this.points as initial point
     lp = this.points.length-1;
     p = this.species.eq(this.points[lp-2], this.points[lp-1], this.points[lp]);
     this.points.push(this.scale * p[0], this.scale * p[1], this.scale * p[2]);
     }*/
            this.create();
        } else if (n < this._pointCount) {
            this.pointCount = this._pointCount = n;
            while (this.points.length / 3 > n) {
                this.points.pop();
                this.points.pop();
                this.points.pop();
            }
        }
        initBuffers();
        return this;
    };

    Attractor.prototype.setPointSize = function(n) {
        this.pointSize = n;
        pointSize = n;
    };

    Attractor.prototype.setBlur = function(n) {
        this.blur = n;
        canvasContainer.find('canvas').css('filter', `blur(${n}px)`);
    };

    Attractor.prototype.create = function() {
        this.points = [];
        var p = [0.0, 0.0, 0.0];
        for (var i = 0, n = this.pointCount; i < n; i++) {
            p = this.species.eq(this, p[0], p[1], p[2]);
            this.points.push(this.scale * p[0], this.scale * p[1], this.scale * p[2]);
        }
        return this;
    };

    Attractor.prototype.setRotSpeed = function(n) {
        rotAccX = n * 0.1;
        rotAccY = n;
    };

    this.initialize = initialize;

    return this;
}
