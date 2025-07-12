## The request data

Contents of `request.json` (conforming to [CoGroupMember Schema](https://spaces.at.internet2.edu/display/COmanage/CoGroupMember+Schema) for a JSON Request)

```json
{
  "RequestType":"CoGroupMembers",
  "Version":"1.0",
  "CoGroupMembers":
  [
    {
      "Version":"1.0",
      "CoGroupId":"1647",
      "Person":
      {
        "Type":"CO",
        "Id":"2969"
      },
      "Member":true,
      "ValidThrough":"2025-07-12T04:55:34Z"
    }
  ]
}
```

1. Note the use of ValidThrough to set an end date for valid membership (this is
   supplied in ISO8601 YYYY-MM-DDTHH:MM::SSZ format i.e. UTC). This COManage
   feature will save us from a heap of work that we'd otherwise need to do in
   an external system to schedule future membership removals.
1. Note the Type is CO and Id was supplied as an integer that I had to look up
   in the registry UI. That's not ideal, and I wonder how to specify the person
   using their (e.g.) sub or ePPN? TODO

## The POST action

```bash
curl -v \
    -d @request.json \
    -X POST \
    -u "${my_user}:${my_key}" \
    -H "Content-Type: application/json" \
    -H "Accept: application/json" \
    --location "https://${my_domain}/registry/co_group_members.json"
```

## The response

```
# HTTP/2 201
{
  "ResponseType":"NewObject",
  "Version":"1.0",
  "ObjectType":"CoGroupMember",
  "Id":"4090"
}
```

## The result

(what this resulted in being created in `co_groups`):

```json
{
  "ResponseType": "CoGroupMembers",
  "Version": "1.0",
  "CoGroupMembers": [
    {
      "Version": "1.0",
      "Id": 4090,
      "CoGroupId": 1647,
      "Person": {
        "Type": "CO",
        "Id": 2969
      },
      "Member": true,
      "ValidThrough": "2025-07-12 04:55:34"
    }
  ]
}
```
