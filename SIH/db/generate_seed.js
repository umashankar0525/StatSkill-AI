// Build the legacy bootstrap seed from the same four-ministry catalogue as the API.
const fs=require('node:fs');
const path=require('node:path');
const catalog=JSON.parse(fs.readFileSync(path.join(__dirname,'../data/role_framework.json'),'utf8'));
const quote=value=>"'"+value.replaceAll("'","''")+"'";
const rows=['BEGIN TRANSACTION;'];
for(const ministry of catalog.ministries){
    rows.push(`INSERT INTO ministries(name,type,state,parent_ministry) VALUES(${quote(ministry.name)},'central',NULL,NULL);`);
    for(const dept of ministry.departments)rows.push(`INSERT INTO ministries(name,type,state,parent_ministry) SELECT ${quote(dept.name)},'central',NULL,id FROM ministries WHERE name=${quote(ministry.name)} AND parent_ministry IS NULL;`);
}
rows.push('COMMIT;');
fs.writeFileSync(path.join(__dirname,'seed.sql'),rows.join('\n')+'\n');
console.log('Generated four ministries and seventeen work areas.');
