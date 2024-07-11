-- as user postgres:
-- psql < drop_and_create_db.sql
-- OR if you have it on docker / k8s: psql -h localhost -U postgres < drop_and_create_db.sql
create user dbwriter with password 'blehbleh';
drop database dbwriter_python;
create database dbwriter_python;
grant all privileges on database dbwriter_python to dbwriter;
-- https://stackoverflow.com/questions/67276391/why-am-i-getting-a-permission-denied-error-for-schema-public-on-pgadmin-4
-- postgres 15+ you need to make the new user own the new database and/or or grant them all privileges on the public schema within the new database
ALTER DATABASE dbwriter_python OWNER TO dbwriter;