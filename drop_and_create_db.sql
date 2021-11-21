-- as user postgres:
-- psql < drop_and_create_db.sql
-- OR if you have it on docker / k8s: psql -h localhost -U postgres < drop_and_create_db.sql
create user dbwriter with password 'blehbleh';
drop database dbwriter_python;
create database dbwriter_python;
grant all privileges on database dbwriter_python to dbwriter;
