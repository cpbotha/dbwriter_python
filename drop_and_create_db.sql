-- as user postgres:
-- psql < drop_and_create_db.sql
create user dbwriter with password 'blehbleh';
drop database dbwriter_python;
create database dbwriter_python;
grant all privileges on database dbwriter_python to dbwriter;
