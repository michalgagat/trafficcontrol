#!/usr/bin/env python3
#
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import argparse
import os
import shlex
import subprocess
import sys

import yaml # PyYAML


PROGRAM_NAME = sys.argv[0]
HOME = os.environ['HOME']

# globals used by commands
DB_NAME     = ''
DB_SUPER_USER = 'postgres'
DB_USER = ''
DB_PASSWORD = ''
HOST_IP     = ''
HOST_PORT   = ''


def parse_dbconf_yml_pg_driver():
    db_conf = None
    with open('db/dbconf.yml') as conf_file:
        db_conf = yaml.safe_load(conf_file)
    db_connection = db_conf[args.environment]
    open_str = db_connection['open']

    db_open = dict(token.split('=') for token in shlex.split(open_str))

    global HOST_IP, HOST_PORT, DB_USER, DB_PASSWORD, DB_NAME
    HOST_IP = db_open['host']
    HOST_PORT = db_open['port']
    DB_USER = db_open['user']
    DB_PASSWORD = db_open['password']
    DB_NAME = db_open['dbname']

def die(message):
    print(message, file=sys.stderr)
    sys.exit(1)

def system(command):
    proc = subprocess.run(command, shell=True, stdout=subprocess.PIPE, universal_newlines=True)
    # TODO: check if Perl backtick system commands print stdout, set defaulted arg print_stdout=True if it doesn't print
    print(proc.stdout)
    return proc

def goose(command='up'):
    print("Migrating database...")
    if system(f"goose --env={args.environment} {command}").returncode != 0:
        die("Can't run goose")

def reset():
    create_user()
    dropdb()
    createdb()
    load_schema()
    goose('up')

def upgrade():
    goose('up')
    seed()
    patch()

def down():
    goose('down')

def redo():
    goose('redo')

def status():
    goose('status')

def dbversion():
    goose('dbversion')

def seed():
    print("Seeding database w/ required data.")
    if system(f"psql -h {HOST_IP} -p {HOST_PORT} -d {DB_NAME} -U {DB_USER} -e -v ON_ERROR_STOP=1 < db/seeds.sql").returncode != 0:
        die("Can't seed database w/ required data")

def patch():
    print("Patching database with required data fixes.")
    if system(f"psql -h {HOST_IP} -p {HOST_PORT} -d {DB_NAME} -U {DB_USER} -e -v ON_ERROR_STOP=1 < db/patches.sql").returncode != 0:
        die("Can't patch database w/ required data")

def load_schema():
    print("Creating database tables.")
    if system(f"psql -h {HOST_IP} -p {HOST_PORT} -d {DB_NAME} -U {DB_USER} -e -v ON_ERROR_STOP=1 < db/create_tables.sql").returncode != 0:
        die("Can't create database tables")

def dropdb():
    print(f"Dropping database: {DB_NAME}")
    if system(f"dropdb -h {HOST_IP} -p {HOST_PORT} -U {DB_SUPER_USER} -e --if-exists {DB_NAME}").returncode != 0:
        die(f"Can't drop db {DB_NAME}")

def createdb():
    db_exists_cmd = f"psql -h {HOST_IP} -U {DB_SUPER_USER} -p {HOST_PORT} -tAc \"SELECT 1 FROM pg_database WHERE datname='{DB_NAME}'\""
    if system(db_exists_cmd).stdout:
        print(f"Database {DB_NAME} already exists")
        return
    cmd = f"createdb -h {HOST_IP} -p {HOST_PORT} -U {DB_SUPER_USER} -e --owner {DB_USER} {DB_NAME}"
    if system(cmd).returncode != 0:
        die(f"Can't create db {DB_NAME}")

def create_user():
    print(f"Creating user: {DB_USER}")
    user_exists_cmd = f"psql -h {HOST_IP} -p {HOST_PORT} -U {DB_SUPER_USER} -tAc \"SELECT 1 FROM pg_roles WHERE rolname='{DB_USER}'\""

    if not system(user_exists_cmd).stdout:
        sql_cmd = f"CREATE USER {DB_USER} WITH LOGIN ENCRYPTED PASSWORD '{DB_PASSWORD}'"
        if system(f"psql -h {HOST_IP} -p {HOST_PORT} -U {DB_SUPER_USER} -etAc \"{sql_cmd}\"").returncode != 0:
            die(f"Can't create user {DB_USER}")

def drop_user():
    if system(f"dropuser -h {HOST_IP} -p {HOST_PORT} -U {DB_SUPER_USER} -i -e {DB_USER}").returncode != 0:
        die(f"Can't drop user {DB_USER}")

def show_users():
    if system(f"psql -h {HOST_IP} -p {HOST_PORT} -U {DB_SUPER_USER} -ec '\\du'").returncode != 0:
        die("Can't show users")

def reverse_schema():
    # TODO: verify that PATH and PERL5LIB stuff
    if system(f"./admin.pl --env={args.environment} reverse_schema").returncode != 0:
        die("Can't run reverse_schema")


if __name__ == '__main__':
	
	usage = ("\n"
	    f"Usage:  {PROGRAM_NAME} [--env (development|test|production|integration)] [arguments]\t\n\n"
	    f"Example:  {PROGRAM_NAME} --env=test reset\n\n"
	    "Purpose:  This script is used to manage database. The environments are\n"
	    "          defined in the dbconf.yml, as well as the database names.\n\n"
	    "NOTE: \n"
	    "Postgres Superuser: The 'postgres' superuser needs to be created to run $PROGRAM_NAME and setup databases.\n"
	    "If the 'postgres' superuser has not been created or password has not been set then run the following commands accordingly. \n\n"
	    "Create the 'postgres' user as a super user (if not created):\n\n"
	    "     $ createuser postgres --superuser --createrole --createdb --login --pwprompt\n\n"
	    f"Modify your {HOME}/.pgpass file which allows for easy command line access by defaulting the user and password for the database\n"
	    "without prompts.\n\n"
	    " Postgres .pgpass file format:\n"
	    " hostname:port:database:username:password\n\n"
	    " ----------------------\n"
	    " Example Contents\n"
	    " ----------------------\n"
	    " *:*:*:postgres:your-postgres-password \n"
	    " *:*:*:traffic_ops:the-password-in-dbconf.yml \n"
	    " ----------------------\n\n"
	    f" Save the following example into this file {HOME}/.pgpass with the permissions of this file\n"
	    " so only your user can read and write.\n\n"
	    f"     $ chmod 0600 {HOME}/.pgpass\n\n"
	    "===================================================================================================================\n"
	    f"{PROGRAM_NAME} arguments:   \n\n"
	    "createdb  - Execute db 'createdb' the database for the current environment.\n"
	    "create_user  - Execute 'create_user' the user for the current environment (traffic_ops).\n"
	    "dropdb  - Execute db 'dropdb' on the database for the current environment.\n"
	    "down  - Roll back a single migration from the current version.\n"
	    "drop_user  - Execute 'drop_user' the user for the current environment (traffic_ops).\n"
        "migrate  - Execute migrate on the database for the current environment.\n"
	    "patch  - Execute sql from db/patches.sql for loading post-migration data patches.\n" 
	    "redo  - Roll back the most recently applied migration, then run it again.\n"
	    "reset  - Execute db 'dropdb', 'createdb', load_schema, migrate on the database for the current environment.\n"
	    "reverse_schema  - Reverse engineer the lib/Schema/Result files from the environment database.\n"
	    "seed  - Execute sql from db/seeds.sql for loading static data.\n"
	    "show_users  - Execute sql to show all of the user for the current environment.\n"
	    "status  - Print the status of all migrations.\n"
	    "upgrade  - Execute migrate, seed, and patches on the database for the current environment.\n")
	
	
	env_choices = (
	    'development',
	    'test',
	    'integration',
	    'production',
	)
	arg_choices = {
	    'createdb': createdb,
	    'dropdb': dropdb,
	    'create_user': create_user,
	    'drop_user': drop_user,
	    'show_users': show_users,
	    'reset': reset,
	    'upgrade': upgrade,
	    'migrate': goose,
	    'down': down,
	    'redo': redo,
	    'status': status,
	    'dbversion': dbversion,
	    'seed': seed,
	    'load_schema': load_schema,
	    'reverse_schema': reverse_schema,
	    'patch': patch,
	}
	
	parser = argparse.ArgumentParser(description='Manage the Traffic Ops database', usage=usage)
	parser.add_argument('--env', dest='environment', default='development', choices=env_choices)
	parser.add_argument('cmd', choices=arg_choices.keys())
	args = parser.parse_args()

	os.environ['MOJO_MODE'] = args.environment

	parse_dbconf_yml_pg_driver();
	os.environ['PGPASSWORD'] = DB_PASSWORD

	arg_choices[args.cmd]()
