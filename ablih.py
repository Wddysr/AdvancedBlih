#!/usr/bin/python3

# Advanced blih : based on blih 1.7
# To-do:
#   - check and clean the legacy code if needed

import os
import sys
import getopt
import hmac
import hashlib
import urllib.request
import urllib.parse
import json
import getpass
import signal
from os.path import expanduser


version = 0.2
CREDENTIALS_DIR = expanduser("~/.blih_credentials") # expanduser("~") = multiplatform home

class blih:
    def __init__(self, baseurl='https://blih.epitech.eu/', user=None, token=None, verbose=False, user_agent='blih-' + str(version)):
        self._baseurl = baseurl
        if user == None:
            self._user = getpass.getuser()
        else:
            self._user = user
        if token == "toSave":
            self.token_calc()
            self.save_credential()
        elif token:
            self._token = token
        elif not self.load_credential():
            self.token_calc()
        self._verbose = verbose
        self._useragent = user_agent

    def token_get(self):
        return self._token

    def token_set(self, token):
        self._token = token

    token = property(token_get, token_set)

    def token_calc(self):
        self._token = bytes(hashlib.sha512(bytes(getpass.getpass(), 'utf8')).hexdigest(), 'utf8')

    def sign_data(self, data=None):
        signature = hmac.new(self._token, msg=bytes(self._user, 'utf8'), digestmod=hashlib.sha512)
        if data:
            signature.update(bytes(json.dumps(data, sort_keys=True, indent=4, separators=(',', ': ')), 'utf8'))

        signed_data = {'user' : self._user, 'signature' : signature.hexdigest()}
        if data != None:
            signed_data['data'] = data

        return signed_data

    def request(self, resource, method='GET', content_type='application/json', data=None, url=None):
        signed_data = self.sign_data(data)

        if url:
            req = urllib.request.Request(url=url, method=method, data=bytes(json.dumps(signed_data), 'utf8'))
        else:
            req = urllib.request.Request(url=self._baseurl + resource, method=method, data=bytes(json.dumps(signed_data), 'utf8'))
        req.add_header('Content-Type', content_type)
        req.add_header('User-Agent', self._useragent)

        try:
            f = urllib.request.urlopen(req)
        except urllib.error.HTTPError as e:
            print ('HTTP Error ' + str(e.code))
            data = json.loads(e.read().decode('utf8'))
            print ("Error message : '" + data['error'] + "'")
            sys.exit(1)

        if f.status == 200:
            try:
                data = json.loads(f.read().decode('utf8'))
            except:
                print ("Can't decode data, aborting")
                sys.exit(1)
            return (f.status, f.reason, f.info(), data)

        print ('Unknown error')
        sys.exit(1)

    def repo_create(self, name, type='git', description=None):
        data = {'name' : name, 'type' : type}
        if description:
            data['description'] = description
        status, reason, headers, data = self.request('/repositories', method='POST', data=data)
        print (data['message'])

    def repo_list(self):
        status, reason, headers, data = self.request('/repositories', method='GET')
        for i in data['repositories']:
            print (i)

    def repo_delete(self, name):
        status, reason, headers, data = self.request('/repository/' + name, method='DELETE')
        print (data['message'])

    def repo_info(self, name):
        status, reason, headers, data = self.request('/repository/' + name, method='GET')
        print (data['message'])

    def repo_setacl(self, name, acluser, acl):
        data = {'user' : acluser, 'acl' : acl}
        status, reason, headers, data = self.request('/repository/' + name + '/acls', method='POST', data=data)
        print (data['message'])

    def repo_getacl(self, name):
        status, reason, headers, data = self.request('/repository/' + name + '/acls', method='GET')
        for i in data.keys():
            print (i + ':' + data[i])

    def sshkey_upload(self, keyfile):
        try:
            f = open(keyfile, 'r')
        except (PermissionError, FileNotFoundError):
            print ("Can't open file : " + keyfile)
            return
        key = urllib.parse.quote(f.read().strip('\n'))
        f.close()
        data = {'sshkey' : key}
        status, reason, headers, data = self.request('/sshkeys', method='POST', data=data)
        print (data['message'])

    def sshkey_delete(self, sshkey):
        status, reason, headers, data = self.request('/sshkey/' + sshkey, method='DELETE')
        print (data['message'])

    def sshkey_list(self):
        status, reason, headers, data = self.request('/sshkeys', method='GET')
        for i in data.keys():
            print (data[i] + ' ' + i)

    def whoami(self):
        status, reason, headers, data = self.request('/whoami', method='GET')
        print (data['message'])
		
    def save_credential(self):
        if not os.path.exists(CREDENTIALS_DIR):
            os.makedirs(CREDENTIALS_DIR)
        f = open(CREDENTIALS_DIR + "/" + self._user, 'wb')
        f.write(self._token)
        f.close()
        
    def load_credential(self):
        if os.path.exists(CREDENTIALS_DIR + '/' + self._user):
            f = open(CREDENTIALS_DIR + "/" + self._user, 'rb')
            self._token = f.read()
            return True
        return False

def usage_repository():
    print ('Usage: ' + sys.argv[0] + ' [options] repository command ...')
    print ()
    print ('Commands :')
    print ('\tcreate repo\t\t\t-- Create a repository named "repo"')
    print ('\tinfo repo\t\t\t-- Get the repository metadata')
    print ('\tgetacl repo\t\t\t-- Get the acls set for the repository')
    print ('\tlist\t\t\t\t-- List the repositories created')
    print ('\tsetacl repo user [acl]\t\t-- Set (or remove) an acl for "user" on "repo"')
    print ('\t\t\t\t\tACL format:')
    print ('\t\t\t\t\tr for read')
    print ('\t\t\t\t\tw for write')
    print ('\t\t\t\t\ta for admin')
    sys.exit(1)

def repository(args, baseurl, user, token, verbose, user_agent):
    if len(args) == 0:
        usage_repository()
    if args[0] == 'create':
        if len(args) != 2:
            usage_repository()
        handle = blih(baseurl=baseurl, user=user, token=token, verbose=verbose, user_agent=user_agent)
        handle.repo_create(args[1])
    elif args[0] == 'list':
        if len(args) != 1:
            usage_repository()
        handle = blih(baseurl=baseurl, user=user, token=token, verbose=verbose, user_agent=user_agent)
        handle.repo_list()
    elif args[0] == 'info':
        if len(args) != 2:
            usage_repository()
        handle = blih(baseurl=baseurl, user=user, token=token, verbose=verbose, user_agent=user_agent)
        handle.repo_info(args[1])
    elif args[0] == 'delete':
        if len(args) != 2:
            usage_repository()
        handle = blih(baseurl=baseurl, user=user, token=token, verbose=verbose, user_agent=user_agent)
        handle.repo_delete(args[1])
    elif args[0] == 'setacl':
        if len(args) != 4 and len(args) != 3:
            usage_repository()
        if len(args) == 3:
            acl = ''
        else:
            acl = args[3]
        handle = blih(baseurl=baseurl, user=user, token=token, verbose=verbose, user_agent=user_agent)
        handle.repo_setacl(args[1], args[2], acl)
    elif args[0] == 'getacl':
        if len(args) != 2:
            usage_repository()
        handle = blih(baseurl=baseurl, user=user, token=token, verbose=verbose, user_agent=user_agent)
        handle.repo_getacl(args[1])
    else:
        usage_repository()

def usage_sshkey():
    print ('Usage: ' + sys.argv[0] + ' [options] sshkey command ...')
    print ()
    print ('Commands :')
    print ('\tupload [file]\t\t\t-- Upload a new ssh-key')
    print ('\tlist\t\t\t\t-- List the ssh-keys')
    print ('\tdelete <sshkey>\t\t\t-- Delete the sshkey with comment <sshkey>')
    sys.exit(1)

def sshkey(args, baseurl, user, token, verbose, user_agent):
    if len(args) == 0:
        usage_sshkey()
    if args[0] == 'list':
        handle = blih(baseurl=baseurl, user=user, token=token, verbose=verbose, user_agent=user_agent)
        handle.sshkey_list()
    elif args[0] == 'upload':
        key = None
        if len(args) == 1:
            key = os.getenv('HOME') + '/.ssh/id_rsa.pub'
        elif len(args) == 2:
            key = args[1]
        else:
            usage_sshkey()
        handle = blih(baseurl=baseurl, user=user, token=token, verbose=verbose, user_agent=user_agent)
        handle.sshkey_upload(key)
    elif args[0] == 'delete':
        if len(args) != 2:
            usage_sshkey()
        handle = blih(baseurl=baseurl, user=user, token=token, verbose=verbose, user_agent=user_agent)
        handle.sshkey_delete(args[1])
    else:
        usage_sshkey()

def whoami(args, baseurl, user, token, verbose, user_agent):
    handle = blih(baseurl=baseurl, user=user, token=token, verbose=verbose, user_agent=user_agent)
    handle.whoami()

def usage():
    print ('Usage: ' + sys.argv[0] + ' [options] command ...')
    print ()
    print ('Global Options :')
    print ('\t-u user | --user=user\t\t-- Run as user')
    print ('\t-v | --verbose\t\t\t-- Verbose')
    print ('\t-b url | --baseurl=url\t\t-- Base URL for BLIH')
    print ('\t-t | --token\t\t\t-- Specify token in the cmdline')
    print ('\t-c | --credential\t\t-- Save the token in a file')
    print ()
    print ('Commands :')
    print ('\trepository\t\t\t-- Repository management')
    print ('\tsshkey\t\t\t\t-- SSH-KEYS management')
    print ('\twhoami\t\t\t\t-- Print who you are')
    sys.exit(1)

def signal_handler(signal, frame):
    print('Ctrl+C pressed, action aborted.')
    sys.exit(0)
    
if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'hvcu:b:t:VU:', ['help', 'verbose', 'credential', 'user=', 'baseurl=', 'token=', 'version', 'useragent='])
    except getopt.GetoptError as e:
        print (e)
        usage()

    verbose = False
    user = None
    baseurl = 'https://blih.epitech.eu/'
    token = None
    user_agent = 'AdvancedBlih-' + str(version)

    for o, a in opts:
        if o in ('-h', '--help'):
            usage()
        elif o in ('-v', '--verbose'):
            verbose = True
        elif o in ('-u', '--user'):
            user = a
        elif o in ('-b', '--baseurl'):
            baseurl = a
        elif o in ('-t', '--token'):
            token = bytes(a, 'utf8')
        elif o in ('-V', '--version'):
            print ('blih version ' + str(version))
            sys.exit(0)
        elif o in ('-U', '--useragent'):
            user_agent = a
        elif o in ('-c', '--credential'):
            token = "toSave"
        else:
            usage()

    if len(args) == 0:
        usage()

    try:
        if args[0] == 'repository':
            repository(args[1:], baseurl, user, token, verbose, user_agent)
        elif args[0] == 'sshkey':
            sshkey(args[1:], baseurl, user, token, verbose, user_agent)
        elif args[0] == 'whoami':
            whoami(args[1:], baseurl, user, token, verbose, user_agent)
        else:
            usage()
    except KeyboardInterrupt:
        print('\nCtrl+C pressed, action aborted.\n')
        sys.exit(0)
    except:
        print('\nAn unexpected error as occured.\n')
        sys.exit(2)