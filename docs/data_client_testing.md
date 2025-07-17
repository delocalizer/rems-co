## Goal

How do **COmanage** group memberships become available in OIDC claims as
issued by CILogon? Let's explore that.

## Example use case

Predicate:
Community agrees that group membership maps to entitlement to a resource.

Use case:
A data provider service registered as an OIDC client (RP) needs to know what
groups a user is a member of, to provide access to the correct dataset(s).

## Configure a dummy data consumer

Log into **COmanage** registry and register a new OIDC client with the following
settings. This will map the `isMemberOf` attribute(s) from the underlying LDAP
database into an OIDC `groups` claim. Note that `groups` is just a name we made
up here.

```
Home URL: http://127.0.0.1               # not used in these tests 
Callback URL: http://127.0.0.1/callback  # not used in these tests
Scopes: openid, profile, email, org.cilogon.userinfo
LDAP to Claim Mappings:
  Connection Details (defaults)
  Search Details (defaults)
  Mappings:
    LDAP Attribute Name: isMemberOf
    OIDC Claim Name: groups
    Multivalued: ✅
```

⚠️**Important**

Take note of your client id and client secret when the client is registered.

## Command-line test

1. Initiate an OIDC "device authorization" flow from your command line:
```bash
export CLIENT_ID=xxxx
export CLIENT_SECRET=xxxx
curl -X POST https://my.cilogon.org/oauth2/device_authorization \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "client_id=$CLIENT_ID" \
    -d "client_secret=$CLIENT_SECRET" \
    -d "scope=openid profile email org.cilogon.userinfo"
```

you'll get back something like this:
```json
{
 "device_code": "XXXX",
 "user_code": "AAA-BBB-CCC",
 "expires_in": 900,
 "interval": 5,
 "verification_uri": "https://my.cilogon.org/device/",
 "verification_uri_complete": "https://my.cilogon.org/device/?user_code=AAA-BBB-CCC"
}
```
1. Now visit the `verification_uri_complete` URL in your browser (or the `verification_uri` then enter the `user_code`) and complete the login.

1. After logging in via the browser, request a token from the token endpoint:
```bash
curl -X POST https://my.cilogon.org/oauth2/token \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "grant_type=urn:ietf:params:oauth:grant-type:device_code" \
    -d "device_code=XXXX" \
    -d "client_id=$CLIENT_ID" \
    -d "client_secret=$CLIENT_SECRET"
```
you'll get back a response:
```json
{
  "access_token":"XXXX",
  "id_token":"YYYY",
  "token_type":"Bearer",
  "expires_in":900
}
```
You can decode the `id_token` JWT component:
```
echo YYYY|jq .id_token|cut -f2 -d .|base64 -d|jq .
```
to get something like:
```json
{
  "sub": "http://cilogon.org/serverI/users/9999",
  "idp_name": "Wonderland University",
  "eppn": "alice@wonderland.edu",
  "iss": "https://my.cilogon.org",
  "groups": [
    "CO:members:all",
    "CO:members:active",
    "urn:test:mri:cooldata"
  ],
  "name": "Alice Liddell",
  "family_name": "Liddell",
  "given_name": "Alice",
  "email": "alice.liddell@wonderland.edu",
  ...
}
```
You see the `groups` is in there and it could be used straight away, but it's
often considered better practice to get authz info not from an identity token
but dynamically from the `userinfo` endpoint:

```bash
ACCESS_TOKEN="XXXX" # access_token from the original token endpoint response
curl https://my.cilogon.org/oauth2/userinfo \
    -H "Authorization: Bearer ${ACCESS_TOKEN}"
```
example response:
```json
{
  "sub": "http://cilogon.org/serverI/users/9999",
  "idp_name": "Wonderland University",
  "iss": "https://my.cilogon.org",
  "groups": [
    "CO:members:active",
    "CO:members:all",
    "urn:test:mri:cooldata"
  ],
  "name": "Alice Liddell",
  "family_name": "Liddell",
  "given_name": "Alice",
  "email": "alice.liddell@wonderland.edu",
  ...
}
```
## What to do with this?

Note that the `groups` claims contains a group `urn:test:mri:cooldata`. This
can be used by the data provider to map to an entitlement to a data asset by
some agreed-upon convention — for example, that the issuer `iss` matches a
trusted issuer, and that the name of the group matches exactly the PID of a
data asset.
