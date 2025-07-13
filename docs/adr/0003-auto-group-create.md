# 3. Auto group create

Date: 2025-07-14

## Status

Accepted

## Context

We need to consider how COmanage groups are created. A related question is what
to do when a user is granted an entitlement on a resource that has no associated
group. Here are some options:
1. All groups are assumed pre-populated in COmanage by some other process. If
   a user is granted an entitlement on a resource with no associated group, log
   a warning only.
1. No groups are assumed pre-populated in COmanage. If a user is granted an
   entitlement on a resource with no associated group, create the group and add
   them.
1. No groups are assumed pre-populated in COmanage. If a user is granted an
   entitlement on a resource with no associated group and the resource id
   contains some special token e.g. `:cogroup`, the group is created and the
   user is added, otherwise no group is created and a warning is logged.
1. No groups are assumed pre-populated in COmanage. If a user is granted an
   entitlement on a resource with no associated group and the resource id
   matches a configurable allow list or pattern (for example, 'urn:my.org:\*') 
   the group is created and the user is added, otherwise no group is created
   and a warning is logged.

## Decision

Two is simple and handles the current use-case; the downside is that there is
no flexibility - any REMS resource entitlement will result in an associated
COmanage group. The third option is flexible and simple but bad when the REMS
resource id is otherwise PID of some kind e.g. a DOI, which shouldn't be
altered. Let's go with the fourth option.

## Consequences

Groups will be created as-needed in COmanage, for resources that are explicitly
allowed.
