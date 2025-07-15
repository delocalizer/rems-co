# rems-co

**rems-co** is a lightweight bridge service that enables entitlement events from the [REMS]
(https://github.com/CSCfi/rems) Resource Entitlement Management System to be reflected in real
time as group membership changes within a COmanage Registry. When a user is approved for access
to a resource in REMS, **rems-co** ensures the user is added to the corresponding group in
COmanage; when access is revoked, the user is removed.

The service supports the automatic creation of COmanage groups for resources that do not yet have
a corresponding group. This behavior can be finely controlled via a configuration setting that
defines which resource name patterns are eligible for automatic creation.

## 📎 See also

- [**REMS project**](https://github.com/CSCfi/rems)
- [`DEVELOP.md`](./DEVELOP.md) — developer setup and testing
- [`CONFIGURE+DEPLOY.md`](./CONFIGURE+DEPLOY.md) — deployment and configuration instructions
