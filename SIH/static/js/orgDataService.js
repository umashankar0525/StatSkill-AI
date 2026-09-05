/* Account choices come exclusively from the backend's scoped catalogue. */
(function(window){
    const catalog=()=>window.store?.state.registrationCatalog||{ministries:[],areas:[]};
    const ministries=()=>catalog().ministries;
    const roles=()=>catalog().areas.flatMap(a=>a.roles.map(r=>({...r,name:r.title})));
    Object.defineProperty(window,'CENTRAL_HIERARCHY',{get:ministries});
    Object.defineProperty(window,'STATE_HIERARCHY',{get:()=>[]});
    Object.defineProperty(window,'OFFICIAL_STATISTICAL_DESIGNATIONS',{get:roles});
    window.getAllMinistriesList=()=>ministries().map(m=>m.name);
    window.getDepartmentsForMinistry=name=>ministries().find(m=>m.name===name)?.departments.map(d=>d.name)||[];
    window.getAllDesignationsList=()=>[...new Set(roles().map(r=>r.title))];
    window.OrgDataService={
        getMinistries:ministries,
        getStatesAndUTs:()=>[],
        getDepartments:(type,id)=>['central','Central Government'].includes(type)?ministries().find(m=>m.id===id||m.name===id)?.departments||[]:[],
        getOrganisations:()=>[],
        getDesignations:(type,mid,area)=>catalog().areas.find(a=>a.id===area||a.name===area)?.roles||[],
        validateFullHierarchy(payload){
            const ministry=ministries().find(m=>m.id===payload.ministry||m.name===payload.ministry);
            const valid=!!ministry&&ministry.departments.some(d=>d.id===payload.department||d.name===payload.department);
            return {valid,error:valid?'':'Choose a supported ministry and work area.'};
        }
    };
})(window);
