const {test,beforeEach,mock}=require('node:test');
const assert=require('node:assert/strict');
process.env.DB_PASSWORD='test-only-never-deploy';
process.env.JWT_SECRET='test-only-secret-at-least-32-characters';
// Process-local database double; no application code or real database is changed.
const dbPath=require.resolve('../src/config/db');
const db={pool:{query:mock.fn()},checkDbConnection:mock.fn()};
require.cache[dbPath]={id:dbPath,filename:dbPath,loaded:true,exports:db};
const request=require('supertest');
const app=require('../src/server');
beforeEach(()=>{
 db.pool.query.mock.resetCalls();db.pool.query.mock.mockImplementation(async()=>[[]]);
 db.checkDbConnection.mock.resetCalls();db.checkDbConnection.mock.mockImplementation(async()=>true);
});
test('liveness is independent of database',async()=>{
 await request(app).get('/healthz').expect(200);
 assert.equal(db.checkDbConnection.mock.callCount(),0);
});
test('readiness rejects unavailable database without leaking details',async()=>{
 db.checkDbConnection.mock.mockImplementation(async()=>{throw new Error('sensitive connection string')});
 const res=await request(app).get('/readyz').expect(503);
 assert.ok(!JSON.stringify(res.body).includes('sensitive'));
});
test('readiness succeeds with database',async()=>{
 await request(app).get('/readyz').expect(200);
});
test('anonymous users cannot create posts',async()=>{
 await request(app).post('/api/posts').send({title:'hello',body:'hello'}).expect(401);
 assert.equal(db.pool.query.mock.callCount(),0);
});
test('invalid registration does not query database',async()=>{
 await request(app).post('/api/auth/register').send({name:'a',email:'invalid',password:'x'}).expect(400);
 assert.equal(db.pool.query.mock.callCount(),0);
});
test('unknown account cannot log in',async()=>{
 await request(app).post('/api/auth/login').send({email:'nobody@example.com',password:'test-password'}).expect(401);
});
test('posts are returned from persistence layer',async()=>{
 let count=0;
 db.pool.query.mock.mockImplementation(async()=>++count===1?[[{id:1,title:'Persisted post'}]]:[[{total:1}]]);
 const res=await request(app).get('/api/posts').expect(200);
 assert.equal(res.body.data[0].title,'Persisted post');
});
