## The request data

Contents of `request.json` (conforming to [CoGroup Schema](https://spaces.at.internet2.edu/display/COmanage/CoGroup+Schema) for a JSON Request)

```json
{
  "RequestType":"CoGroups",
  "Version":"1.0",
  "CoGroups":
  [
    {
      "Version":"1.0",
      "CoId":"42",
      "Name":"urn:test:au.org.biocommons:36ca9f7a-df70-458c-a9f3-662e5a7fb15c",
      "Description":"Group associated with read access to resource urn:test:au.org.biocommons:36ca9f7a-df70-458c-a9f3-662e5a7fb15c",
      "Open":false,
      "Status":"Active"
    }
  ]
}
```

## The POST action

```bash
curl -v \
    -d @request.json \
    -X POST \
    -u "${my_user}:${my_key}" \
    -H "Content-Type: application/json" \
    -H "Accept: application/json" \
    --location "https://${my_domain}/registry/co_groups.json"
```

## The response

```
# HTTP/2 201
{
  "ResponseType":"NewObject",
  "Version":"1.0",
  "ObjectType":"CoGroup",
  "Id":"1647"
}
```

## The result

(what this resulted in being created in `co_groups`):

```json
{
  "Version": "1.0",
  "Id": 1647,
  "CoId": 42,
  "Name": "urn:test:au.org.biocommons:36ca9f7a-df70-458c-a9f3-662e5a7fb15c",
  "Description": "Group associated with read access to resource urn:test:au.org.biocommons:36ca9f7a-df70-458c-a9f3-662e5a7fb15c",
  "Open": false,
  "Status": "Active",
  "GroupType": "S",
  "Auto": false,
  "Created": "2025-07-12 03:21:12",
  "Modified": "2025-07-12 03:21:12",
  "Revision": 0,
  "Deleted": false,
  "ActorIdentifier": "xxxx"
}
```

Note that many of these keys were not explicitly set in the request and are
auto-increments, defaults or calculated values: Id, GroupType, Auto, etc.
