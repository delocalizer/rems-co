
There are two COmanage APIs

[The REST API v1](https://spaces.at.internet2.edu/display/COmanage/REST+API+v1)

[The CORE API](https://spaces.at.internet2.edu/display/COmanage/Core+API)

## REST API

This provides the usual create/delete/list/view methods.

Some examples follow:

Prerequisite: `my_user` is a privileged CO API user (but not a platform API user)

Example: [list the COUs in my CO in JSON format](https://spaces.at.internet2.edu/display/COmanage/COU+API#COUAPI-View%28perCO%29)
```bash
curl -u "${my_user}:${my_key}" \
    -H "Content-Type: application/json"\
    -H "Accept: application/json"\
    --location "https://${my_domain}/registry/cous.json?coid=${coid}" \
    | jq .
```

Example [list the Groups in my CO in JSON format](https://spaces.at.internet2.edu/display/COmanage/CoGroup+API#CoGroupAPI-View%28perCO%29)
```bash
curl -u "${my_user}:${my_key}" \
    -H "Content-Type: application/json"\
    -H "Accept: application/json"\
    --location "https://${my_domain}/registry/co_groups.json?coid=${coid}" \
    | jq .
```

Example [view one Group (in my CO) in JSON format](https://spaces.at.internet2.edu/display/COmanage/CoGroup+API#CoGroupAPI-View%28one%29)
```bash
curl -u "${my_user}:${my_key}" \
    -H "Content-Type: application/json"\
    -H "Accept: application/json"\
    --location "https://${my_domain}/registry/co_groups/${groupid}.json" \
    | jq .
```

Example [list the Members in a Group (in my CO) in JSON format](https://spaces.at.internet2.edu/display/COmanage/CoGroupMember+API#CoGroupMemberAPI-View%28perCoGroup%29)
```bash
curl -u "${my_user}:${my_key}" \
    -H "Content-Type: application/json"\
    -H "Accept: application/json"\
    --location "https://${my_domain}/registry/co_group_members.json?cogroupid=${groupid}" \
    | jq .
```

## Core API
This is
> a collection of higher level APIs that provide transaction-oriented operations,
> rather than the lower level, model-oriented REST API v1.
These endpoints must be [enabled](https://spaces.at.internet2.edu/display/COmanage/Core+API#CoreAPI-EnablingCoreAPIs) and associated with unprivileged API users.
