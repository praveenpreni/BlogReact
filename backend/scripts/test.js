const fs=require('node:fs');
const {spawnSync}=require('node:child_process');
fs.mkdirSync('coverage',{recursive:true});
const result=spawnSync(process.execPath,[
 '--test','--experimental-test-coverage',
 '--test-coverage-include=src/**/*.js',
 '--test-reporter=spec','--test-reporter-destination=stdout',
 '--test-reporter=lcov','--test-reporter-destination=coverage/lcov.info',
 'tests/api.test.js'
],{stdio:'inherit'});
if(result.error){console.error(result.error.message);process.exit(1)}
process.exit(result.status??1);
