(function(window,document){
'use strict';
if(!window||!document){return;}

var QUALITY={
  high:{pixelRatioCap:1.75,targetFps:60,shadow:true},
  medium:{pixelRatioCap:1.25,targetFps:40,shadow:true},
  low:{pixelRatioCap:1,targetFps:24,shadow:false}
};
var STATE_DURATIONS={greet:1900,alert:1500,celebrate:2200,speak:2400,listen:1600,'point-left':1800,'point-right':1800,'turn-left':1200,'turn-right':1200,explain:2200,walk:2500};

function identity4(){return [1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1];}
function multiply4(a,b){
  var out=new Array(16),r,c;
  for(c=0;c<4;c++)for(r=0;r<4;r++)out[c*4+r]=a[0*4+r]*b[c*4+0]+a[1*4+r]*b[c*4+1]+a[2*4+r]*b[c*4+2]+a[3*4+r]*b[c*4+3];
  return out;
}
function translation(x,y,z){var m=identity4();m[12]=x;m[13]=y;m[14]=z;return m;}
function scale4(x,y,z){var m=identity4();m[0]=x;m[5]=y;m[10]=z;return m;}
function rotateX(a){var c=Math.cos(a),s=Math.sin(a),m=identity4();m[5]=c;m[6]=s;m[9]=-s;m[10]=c;return m;}
function rotateY(a){var c=Math.cos(a),s=Math.sin(a),m=identity4();m[0]=c;m[2]=-s;m[8]=s;m[10]=c;return m;}
function rotateZ(a){var c=Math.cos(a),s=Math.sin(a),m=identity4();m[0]=c;m[1]=s;m[4]=-s;m[5]=c;return m;}
function transform(t,r,s){var m=translation(t[0],t[1],t[2]);m=multiply4(m,rotateZ(r[2]||0));m=multiply4(m,rotateY(r[1]||0));m=multiply4(m,rotateX(r[0]||0));return multiply4(m,scale4(s[0],s[1],s[2]));}
function perspective(fov,aspect,near,far){
  var f=1/Math.tan(fov/2),nf=1/(near-far),m=new Array(16);
  m[0]=f/aspect;m[1]=0;m[2]=0;m[3]=0;m[4]=0;m[5]=f;m[6]=0;m[7]=0;m[8]=0;m[9]=0;m[10]=(far+near)*nf;m[11]=-1;m[12]=0;m[13]=0;m[14]=2*far*near*nf;m[15]=0;return m;
}
function ease(t){t=Math.max(0,Math.min(1,t));return t*t*(3-2*t);}
function clamp(v,a,b){return Math.max(a,Math.min(b,v));}

function compile(gl,type,source){var shader=gl.createShader(type);gl.shaderSource(shader,source);gl.compileShader(shader);if(!gl.getShaderParameter(shader,gl.COMPILE_STATUS)){throw new Error(gl.getShaderInfoLog(shader)||'shader compile failed');}return shader;}
function createProgram(gl){
  var vs=compile(gl,gl.VERTEX_SHADER,'attribute vec3 aPosition;uniform mat4 uMVP;void main(){gl_Position=uMVP*vec4(aPosition,1.0);}');
  var fs=compile(gl,gl.FRAGMENT_SHADER,'precision mediump float;uniform vec4 uColor;void main(){gl_FragColor=uColor;}');
  var p=gl.createProgram();gl.attachShader(p,vs);gl.attachShader(p,fs);gl.linkProgram(p);if(!gl.getProgramParameter(p,gl.LINK_STATUS)){throw new Error(gl.getProgramInfoLog(p)||'program link failed');}return p;
}
function boxMesh(gl){
  var v=new Float32Array([-1,-1,-1,1,-1,-1,1,1,-1,-1,1,-1,-1,-1,1,1,-1,1,1,1,1,-1,1,1]);
  var i=new Uint16Array([0,1,2,0,2,3,4,6,5,4,7,6,0,4,5,0,5,1,3,2,6,3,6,7,1,5,6,1,6,2,0,3,7,0,7,4]);
  return uploadMesh(gl,v,i);
}
function sphereMesh(gl,lat,longs){
  var verts=[],idx=[],la,lo,theta,phi;
  for(la=0;la<=lat;la++){theta=la*Math.PI/lat;for(lo=0;lo<=longs;lo++){phi=lo*2*Math.PI/longs;verts.push(Math.sin(theta)*Math.cos(phi),Math.cos(theta),Math.sin(theta)*Math.sin(phi));}}
  for(la=0;la<lat;la++)for(lo=0;lo<longs;lo++){var a=la*(longs+1)+lo,b=a+longs+1;idx.push(a,b,a+1,b,b+1,a+1);}
  return uploadMesh(gl,new Float32Array(verts),new Uint16Array(idx));
}
function uploadMesh(gl,verts,idx){var vb=gl.createBuffer(),ib=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,vb);gl.bufferData(gl.ARRAY_BUFFER,verts,gl.STATIC_DRAW);gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER,ib);gl.bufferData(gl.ELEMENT_ARRAY_BUFFER,idx,gl.STATIC_DRAW);return {vb:vb,ib:ib,count:idx.length};}

function Node(name,mesh,color,t,r,s){this.name=name;this.mesh=mesh||null;this.color=color||[1,1,1,1];this.t=t||[0,0,0];this.r=r||[0,0,0];this.s=s||[1,1,1];this.children=[];this.baseR=this.r.slice();this.baseT=this.t.slice();}
Node.prototype.add=function(child){this.children.push(child);return child;};

function LivenzaHost3D(){
  this.rootEl=document.getElementById('livenza3dHost');this.mount=document.getElementById('livenza3dCanvasMount');this.status=document.getElementById('livenza3dStatus');
  this.canvas=null;this.gl=null;this.program=null;this.meshes={};this.rootNode=null;this.joints={};this.running=false;this.raf=0;this.lastFrame=0;this.stateStarted=Date.now();this.stateMachine=window.LivenzaHostStateMachine?new window.LivenzaHostStateMachine():null;this.handlers=[];this.qualityName='high';this.quality=QUALITY.high;this.preferences={enabled:true,intensity:'full',size:'medium',position:'bottom-right'};
}
LivenzaHost3D.prototype.readPreferences=function(){
  if(!this.rootEl)return;var raw=this.rootEl.getAttribute('data-host-preferences');if(raw){try{var parsed=JSON.parse(raw);for(var k in parsed)if(Object.prototype.hasOwnProperty.call(parsed,k))this.preferences[k]=parsed[k];}catch(e){}}
  this.rootEl.classList.remove('host-size-small','host-size-medium','host-size-large','host-pos-bottom-left','host-pos-bottom-right');
  this.rootEl.classList.add('host-size-'+(this.preferences.size||'medium'));this.rootEl.classList.add('host-pos-'+(this.preferences.position||'bottom-right'));
  var shell=this.rootEl.parentElement;if(shell){shell.classList.remove('host-pos-bottom-left','host-pos-bottom-right','host-shell-size-small','host-shell-size-medium','host-shell-size-large');shell.classList.add('host-pos-'+(this.preferences.position||'bottom-right'));shell.classList.add('host-shell-size-'+(this.preferences.size||'medium'));}
};
LivenzaHost3D.prototype.pickQuality=function(){var cap=window.LivenzaCapability||{};if(cap.quality==='low'||cap.lowGpu||cap.isTV){this.qualityName='low';}else if(cap.quality==='medium'||cap.weakDevice){this.qualityName='medium';}else this.qualityName='high';this.quality=QUALITY[this.qualityName];};
LivenzaHost3D.prototype.fail=function(message){if(this.mount)this.mount.hidden=true;if(this.status){this.status.hidden=false;this.status.textContent=message||'3D rendering is unavailable on this browser.';}if(this.rootEl)this.rootEl.classList.add('host3d-unavailable');};
LivenzaHost3D.prototype.init=function(){
  if(!this.rootEl||!this.mount)return false;this.readPreferences();if(this.preferences.enabled===false||this.preferences.enabled==='false'){this.rootEl.hidden=true;return false;}this.pickQuality();
  var canvas=document.createElement('canvas');canvas.className='livenza3d-canvas';canvas.setAttribute('aria-label','Interactive 3D Livenza host');canvas.setAttribute('tabindex','0');this.mount.innerHTML='';this.mount.appendChild(canvas);this.canvas=canvas;
  var gl=canvas.getContext('webgl',{alpha:true,antialias:this.qualityName!=='low',powerPreference:'low-power'})||canvas.getContext('experimental-webgl');if(!gl){this.fail('This browser could not start the 3D Livenza host. All other controls remain available.');return false;}this.gl=gl;
  try{this.program=createProgram(gl);}catch(e){this.fail('The 3D Livenza host could not initialize.');return false;}
  this.aPosition=gl.getAttribLocation(this.program,'aPosition');this.uMVP=gl.getUniformLocation(this.program,'uMVP');this.uColor=gl.getUniformLocation(this.program,'uColor');this.meshes.box=boxMesh(gl);this.meshes.sphere=sphereMesh(gl,this.qualityName==='low'?8:12,this.qualityName==='low'?10:16);this.buildCharacter();this.bind();this.resize();if(this.status)this.status.hidden=true;this.start();return true;
};
LivenzaHost3D.prototype.buildCharacter=function(){
  var B=this.meshes.box,S=this.meshes.sphere;var navy=[0.035,0.12,0.22,1],navy2=[0.05,0.22,0.38,1],white=[0.94,0.97,1,1],skin=[0.72,0.47,0.33,1],dark=[0.08,0.09,0.12,1],blue=[0.05,0.46,0.72,1],shoe=[0.04,0.05,0.07,1];
  var root=new Node('root',null,null,[0,-1.55,0],[0,0,0],[1,1,1]);this.rootNode=root;
  var hip=root.add(new Node('hip',B,navy,[0,1.9,0],[0,0,0],[0.44,0.26,0.23]));
  var torso=hip.add(new Node('torso',B,navy,[0,0.85,0],[0,0,0],[0.62,0.78,0.32]));
  torso.add(new Node('shirt',B,white,[0,0.05,0.34],[0,0,0],[0.28,0.57,0.035]));
  torso.add(new Node('badge',B,blue,[0.35,0.26,0.36],[0,0,0],[0.10,0.12,0.035]));
  var neck=torso.add(new Node('neck',B,skin,[0,0.9,0],[0,0,0],[0.16,0.18,0.15]));
  var headPivot=neck.add(new Node('headPivot',null,null,[0,0.38,0],[0,0,0],[1,1,1]));
  headPivot.add(new Node('head',S,skin,[0,0.33,0],[0,0,0],[0.38,0.46,0.36]));
  headPivot.add(new Node('hair',S,dark,[0,0.62,-0.02],[0,0,0],[0.39,0.18,0.37]));
  headPivot.add(new Node('eyeL',S,white,[-0.15,0.38,0.32],[0,0,0],[0.065,0.055,0.035]));headPivot.add(new Node('pupilL',S,dark,[-0.15,0.38,0.355],[0,0,0],[0.026,0.030,0.018]));
  headPivot.add(new Node('eyeR',S,white,[0.15,0.38,0.32],[0,0,0],[0.065,0.055,0.035]));headPivot.add(new Node('pupilR',S,dark,[0.15,0.38,0.355],[0,0,0],[0.026,0.030,0.018]));
  headPivot.add(new Node('browL',B,dark,[-0.15,0.49,0.35],[0,0,0],[0.11,0.018,0.018]));headPivot.add(new Node('browR',B,dark,[0.15,0.49,0.35],[0,0,0],[0.11,0.018,0.018]));
  var jawPivot=headPivot.add(new Node('jawPivot',null,null,[0,0.18,0.31],[0,0,0],[1,1,1]));jawPivot.add(new Node('mouth',B,[0.28,0.05,0.06,1],[0,0,0.055],[0,0,0],[0.13,0.025,0.018]));
  function arm(side){var sign=side==='left'?-1:1,name=side==='left'?'left':'right';var shoulder=torso.add(new Node(name+'Shoulder',null,null,[sign*0.72,0.57,0],[0,0,0],[1,1,1]));var upper=shoulder.add(new Node(name+'UpperArm',B,navy2,[sign*0.13,-0.38,0],[0,0,0],[0.17,0.42,0.18]));var elbow=upper.add(new Node(name+'Elbow',null,null,[0,-0.92,0],[0,0,0],[1,1,1]));var fore=elbow.add(new Node(name+'Forearm',B,navy,[0,-0.35,0],[0,0,0],[0.15,0.38,0.16]));fore.add(new Node(name+'Hand',S,skin,[0,-0.52,0],[0,0,0],[0.18,0.22,0.16]));return {shoulder:shoulder,elbow:elbow};}
  function leg(side){var sign=side==='left'?-1:1,name=side==='left'?'left':'right';var hp=hip.add(new Node(name+'Hip',null,null,[sign*0.27,-0.25,0],[0,0,0],[1,1,1]));var thigh=hp.add(new Node(name+'Thigh',B,navy,[0,-0.62,0],[0,0,0],[0.23,0.64,0.23]));var knee=thigh.add(new Node(name+'Knee',null,null,[0,-1.30,0],[0,0,0],[1,1,1]));var lower=knee.add(new Node(name+'LowerLeg',B,navy2,[0,-0.58,0],[0,0,0],[0.21,0.58,0.21]));lower.add(new Node(name+'Foot',B,shoe,[0,-0.68,0.18],[0,0,0],[0.24,0.13,0.40]));return {hip:hp,knee:knee};}
  var la=arm('left'),ra=arm('right'),ll=leg('left'),rl=leg('right');this.joints={headPivot:headPivot,jawPivot:jawPivot,leftShoulder:la.shoulder,rightShoulder:ra.shoulder,leftElbow:la.elbow,rightElbow:ra.elbow,leftHip:ll.hip,rightHip:rl.hip,leftKnee:ll.knee,rightKnee:rl.knee,torso:torso,hip:hip};
};
LivenzaHost3D.prototype.resetPose=function(){for(var k in this.joints){if(this.joints[k]){this.joints[k].r=this.joints[k].baseR.slice();this.joints[k].t=this.joints[k].baseT.slice();}}};
LivenzaHost3D.prototype.animatePose=function(now){
  if(!this.stateMachine)return;var state=this.stateMachine.current(),elapsed=now-this.stateMachine.changedAt(),t=elapsed/1000,j=this.joints;this.resetPose();var intensity=this.preferences.intensity||'full';if(intensity==='static'){return;}
  var amp=intensity==='gentle'?0.55:1;var breathe=Math.sin(t*2.0)*0.018*amp;j.torso.s=[j.torso.s[0],j.torso.s[1]+breathe,j.torso.s[2]];
  if(state==='idle'){j.headPivot.r[1]=Math.sin(t*0.45)*0.06*amp;j.leftShoulder.r[2]=-0.04+Math.sin(t*0.7)*0.02;j.rightShoulder.r[2]=0.04-Math.sin(t*0.7)*0.02;}
  else if(state==='greet'){var w=Math.sin(t*8)*0.38*amp;j.rightShoulder.r[2]=-1.25;j.rightShoulder.r[0]=0.25;j.rightElbow.r[0]=-1.15+w;j.headPivot.r[1]=-0.12;}
  else if(state==='walk'){var sw=Math.sin(t*6)*0.55*amp;j.leftHip.r[0]=sw;j.rightHip.r[0]=-sw;j.leftShoulder.r[0]=-sw*0.65;j.rightShoulder.r[0]=sw*0.65;j.leftKnee.r[0]=Math.max(0,-sw)*0.45;j.rightKnee.r[0]=Math.max(0,sw)*0.45;this.rootNode.t[0]=Math.sin(t*1.3)*0.08;}
  else if(state==='point-left'){j.leftShoulder.r[2]=1.25;j.leftShoulder.r[0]=-0.25;j.leftElbow.r[0]=-0.15;j.headPivot.r[1]=0.35;}
  else if(state==='point-right'){j.rightShoulder.r[2]=-1.25;j.rightShoulder.r[0]=-0.25;j.rightElbow.r[0]=-0.15;j.headPivot.r[1]=-0.35;}
  else if(state==='explain'){j.leftShoulder.r[2]=0.72+Math.sin(t*3)*0.12;j.rightShoulder.r[2]=-0.72-Math.sin(t*3+1)*0.12;j.leftElbow.r[0]=-0.55;j.rightElbow.r[0]=-0.55;j.headPivot.r[1]=Math.sin(t*1.5)*0.1;}
  else if(state==='alert'){var a=Math.sin(t*12)*0.08;j.torso.r[1]=a;j.leftShoulder.r[2]=0.65;j.rightShoulder.r[2]=-0.65;j.headPivot.r[0]=-0.12;}
  else if(state==='celebrate'){j.leftShoulder.r[2]=1.95;j.rightShoulder.r[2]=-1.95;j.leftElbow.r[0]=-0.25;j.rightElbow.r[0]=-0.25;j.hip.t[1]=j.hip.baseT[1]+Math.abs(Math.sin(t*4))*0.08;}
  else if(state==='listen'){j.headPivot.r[2]=-0.16;j.headPivot.r[0]=0.08;j.leftShoulder.r[2]=0.14;j.rightShoulder.r[2]=-0.14;}
  else if(state==='speak'){j.jawPivot.r[0]=0.10+Math.abs(Math.sin(t*10))*0.18;j.leftShoulder.r[2]=0.35+Math.sin(t*2.6)*0.08;j.rightShoulder.r[2]=-0.30-Math.sin(t*2.2)*0.08;}
  else if(state==='turn-left'){j.headPivot.r[1]=0.55*ease(Math.min(1,elapsed/500));j.torso.r[1]=0.18;}
  else if(state==='turn-right'){j.headPivot.r[1]=-0.55*ease(Math.min(1,elapsed/500));j.torso.r[1]=-0.18;}
  if(STATE_DURATIONS[state]&&elapsed>STATE_DURATIONS[state])this.stateMachine.complete();
};
LivenzaHost3D.prototype.drawNode=function(node,parent,pv){
  var local=transform(node.t,node.r,node.s),world=multiply4(parent,local),gl=this.gl;
  if(node.mesh){var mvp=multiply4(pv,world);gl.bindBuffer(gl.ARRAY_BUFFER,node.mesh.vb);gl.enableVertexAttribArray(this.aPosition);gl.vertexAttribPointer(this.aPosition,3,gl.FLOAT,false,0,0);gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER,node.mesh.ib);gl.uniformMatrix4fv(this.uMVP,false,new Float32Array(mvp));gl.uniform4fv(this.uColor,new Float32Array(node.color));gl.drawElements(gl.TRIANGLES,node.mesh.count,gl.UNSIGNED_SHORT,0);}
  for(var i=0;i<node.children.length;i++)this.drawNode(node.children[i],world,pv);
};
LivenzaHost3D.prototype.render=function(now){
  if(!this.gl||!this.canvas)return;var gl=this.gl,w=this.canvas.width,h=this.canvas.height;gl.viewport(0,0,w,h);gl.clearColor(0,0,0,0);gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);gl.enable(gl.DEPTH_TEST);gl.enable(gl.BLEND);gl.blendFunc(gl.SRC_ALPHA,gl.ONE_MINUS_SRC_ALPHA);gl.useProgram(this.program);this.animatePose(now||Date.now());var proj=perspective(Math.PI/4,w/Math.max(1,h),0.1,50),view=translation(0,-0.35,-8.2),pv=multiply4(proj,view);this.drawNode(this.rootNode,identity4(),pv);
};
LivenzaHost3D.prototype.loop=function(ts){if(!this.running)return;var interval=1000/this.quality.targetFps;if(ts-this.lastFrame>=interval){this.lastFrame=ts;this.render(Date.now());}var self=this;this.raf=window.requestAnimationFrame(function(n){self.loop(n);});};
LivenzaHost3D.prototype.start=function(){if(this.running||!this.gl)return;this.running=true;var self=this;this.raf=window.requestAnimationFrame(function(n){self.loop(n);});};
LivenzaHost3D.prototype.stop=function(){this.running=false;if(this.raf){window.cancelAnimationFrame(this.raf);this.raf=0;}for(var i=0;i<this.handlers.length;i++){var h=this.handlers[i];h[0].removeEventListener(h[1],h[2]);}this.handlers=[];};
LivenzaHost3D.prototype.resize=function(){if(!this.canvas||!this.mount)return;var rect=this.mount.getBoundingClientRect(),dpr=Math.min(window.devicePixelRatio||1,this.quality.pixelRatioCap),w=Math.max(1,Math.floor(rect.width*dpr)),h=Math.max(1,Math.floor(rect.height*dpr));if(this.canvas.width!==w||this.canvas.height!==h){this.canvas.width=w;this.canvas.height=h;this.canvas.style.width=rect.width+'px';this.canvas.style.height=rect.height+'px';this.render(Date.now());}};
LivenzaHost3D.prototype.requestState=function(name,payload){if(!this.stateMachine)return {accepted:false};var r=name==='wake'?this.stateMachine.wake():this.stateMachine.request(name,payload||{});if(r.accepted)this.stateStarted=Date.now();return r;};
LivenzaHost3D.prototype.pointAt=function(selector,direction){var el=document.querySelector(selector);if(!el)return false;var rect=el.getBoundingClientRect();if(rect.width<=0||rect.height<=0||rect.bottom<0||rect.top>window.innerHeight)return false;return this.requestState(direction==='left'?'point-left':'point-right',{selector:selector}).accepted;};
LivenzaHost3D.prototype.bind=function(){
  var self=this;
  function on(target,type,fn){target.addEventListener(type,fn);self.handlers.push([target,type,fn]);}
  on(window,'resize',function(){self.resize();});
  on(window,'livenza:host-event',function(ev){var d=ev&&ev.detail?ev.detail:{};if(!d.type)return;if(d.source==='operations'&&self.preferences.operational_updates===false)return;if(d.source==='weather'&&self.preferences.weather_reactions===false)return;if(d.source==='motivation'&&self.preferences.motivational_messages===false)return;self.requestState(d.type,d);});
  if(this.canvas){on(this.canvas,'pointerdown',function(ev){ev.preventDefault();self.requestState('listen');var btn=document.getElementById('mascotCompanionButton');if(btn)btn.click();});on(this.canvas,'keydown',function(ev){var k=ev.key||ev.keyCode;if(k==='Enter'||k===' '||k===13||k===32){ev.preventDefault();self.requestState('listen');var btn=document.getElementById('mascotCompanionButton');if(btn)btn.click();}});}
};

var host=new LivenzaHost3D();window.LivenzaHost3D=host;window.LivenzaHost3DClass=LivenzaHost3D;
function boot(){host.init();}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else boot();
})(window,document);
