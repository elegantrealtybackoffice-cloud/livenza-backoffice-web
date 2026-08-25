(function(root,factory){
  var HostStateMachine=factory();
  if(typeof module==='object'&&module.exports){module.exports=HostStateMachine;}
  if(root){root.LivenzaHostStateMachine=HostStateMachine;}
}(typeof window!=='undefined'?window:this,function(){
  var PRIORITY={sleep:100,alert:90,celebrate:80,speak:70,listen:65,greet:60,'point-left':55,'point-right':55,'turn-left':45,'turn-right':45,explain:40,walk:30,idle:0};
  var NON_LOOPING={alert:1,celebrate:1,speak:1,listen:1,greet:1,'point-left':1,'point-right':1,'turn-left':1,'turn-right':1,explain:1,walk:1};
  function HostStateMachine(){this._state='idle';this._payload={};this._changedAt=Date.now();}
  HostStateMachine.PRIORITY=PRIORITY;
  HostStateMachine.prototype.current=function(){return this._state;};
  HostStateMachine.prototype.payload=function(){return this._payload||{};};
  HostStateMachine.prototype.changedAt=function(){return this._changedAt;};
  HostStateMachine.prototype.request=function(name,payload){
    name=String(name||'idle');
    if(PRIORITY[name]===undefined){return {accepted:false,state:this._state,reason:'unknown-state'};}
    if(this._state==='sleep'&&name!=='idle'&&name!=='sleep'){return {accepted:false,state:this._state,reason:'sleeping'};}
    if(name!=='idle'&&PRIORITY[name]<PRIORITY[this._state]){return {accepted:false,state:this._state,reason:'lower-priority'};}
    this._state=name;this._payload=payload||{};this._changedAt=Date.now();
    return {accepted:true,state:this._state};
  };
  HostStateMachine.prototype.complete=function(){
    if(this._state==='sleep'){return {accepted:false,state:'sleep'};}
    if(NON_LOOPING[this._state]||this._state!=='idle'){
      this._state='idle';this._payload={};this._changedAt=Date.now();
    }
    return {accepted:true,state:this._state};
  };
  HostStateMachine.prototype.wake=function(){this._state='idle';this._payload={};this._changedAt=Date.now();return {accepted:true,state:'idle'};};
  return HostStateMachine;
}));
