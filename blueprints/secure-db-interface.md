# Traffic Ops Plugin Interface for Secret Data Store

## Problem Description

Currently, Riak is the only supported data store for *secrets* and their
related data (e.g. public and private keys, certificates, URI signing keys,
etc) in Traffic Ops. The future of Riak is uncertain, so it would be wise to
start preparing Traffic Ops for other potential data stores such as HashiCorp
Vault. There is also a need for an easier way to test and develop TO API
endpoints that require Riak, without actually requiring a running Riak
installation. For instance, it would be useful to have a simple in-memory
and/or file-based key/value store to mock Riak.

## Proposed Change

Within Traffic Ops Go, a new `SecureDB` interface will be defined with the
minimum set of methods to read from and write to any secure data store. The
existing Riak implementation will be refactored into a concrete implementation
of the `SecureDB` interface so that no external functionality will be lost when
using the Riak implementation.

Once the existing Riak implementation has been refactored to implement the
`SecureDB` interface, a *new* memory-based implementation of the `SecureDB`
interface will be added. This implementation is meant to be the simplest
concrete implementation of the `SecureDB` interface that can be used for
testing and development purposes. Basically, any generated or added
certificates (and other secrets currently stored in Riak today) will only exist
in TO memory and will be lost once TO is stopped. The in-memory implementation
will allow easier testing of Riak-related API endpoints where we don't
necessarily need to test the actual reading/writing to Riak as a data store.
For instance, we might care more about testing the generation of a certificate
and its validity as an external API user but not necessarily about the ability
of Riak to store and read data (which we already know it does very well).

This will better separate the concerns of reading/writing data to Riak or some
other secure data store and everything outside of that (the creation of the
data, API input validation, etc). Adding the ability to use a new secure data
store would then be mainly just implementing the read/write integration between
TO and the new data store, without having to worry about everything else in
between the TO API and reading/writing to the data store.

The desired `SecureDB` backend implementation would be chosen by a new TO
configuration option, and any new configuration required for the various
`SecureDB` backends would be contained in configuration files that are separate
from the main `cdn.conf` file, similar to how `riak.conf` contains the
necessary Riak configuration today. Some backends, like the in-memory backend,
may not require any configuration at all and won't have an associated
configuration file.

In order to *swap* `SecureDB` backends, e.g. from Riak to HashiCorp Vault, an
operator would have to stand up Vault, copy all the data from Riak to Vault,
stop Traffic Ops, reconfigure the `SecureDB` backend from Riak to Vault, add
the necessary Vault-specific configuration, start Traffic Ops, and verify that
all the "secure" TO API endpoints return and write the same data as the TO
instance using the Riak backend. This would be done best by standing up two TO
instance side-by-side, one configured for Riak and the other configured for
Vault, and mirroring requests between both instances and comparing results.

### Traffic Portal Impact

n/a

### Traffic Ops Impact

See Proposed Change above.

#### REST API Impact

There are a handful of endpoints that are Riak-specific:
- GET /api/$version/keys/ping (doesn't say "riak" but is almost identical to /riak/ping)
- GET /api/$version/riak/ping
- GET /api/$version/riak/bucket/#bucket/key/#key/values
- GET /api/$version/riak/stats

If Riak is not enabled as the `SecureDB` backend, then these endpoints are not
very useful. It might be advantageous to have similar endpoints that would
apply to *any* of the `SecureDB` backends (for e.g. "ping the secure data store
to verify it's alive" or "get the value for this key from the secure data
store"), but I don't think those endpoints would necessarily be in the scope of
this blueprint.

There are several endpoints that are not Riak-specific but that the TO API
currently uses Riak for:
- GET /api/$version/cdns/name/:name/sslkeys
- GET /api/$version/deliveryservices/xmlId/#xmlid/sslkeys
- GET /api/$version/deliveryservices/hostname/#hostname/sslkeys
- POST /api/$version/deliveryservices/sslkeys/generate
- POST /api/$version/deliveryservices/sslkeys/add
- GET /api/$version/deliveryservices/xmlId/:xmlid/sslkeys/delete
- POST /api/$version/deliveryservices/xmlId/:xmlId/urlkeys/generate
- POST /api/$version/deliveryservices/xmlId/:xmlId/urlkeys/copyFromXmlId/:copyFromXmlId
- GET /api/$version/deliveryservices/xmlId/:xmlId/urlkeys
- GET /api/$version/deliveryservices/:id/urlkeys
- GET /api/$version/cdns/name/:name/dnsseckeys
- POST /api/$version/cdns/dnsseckeys/generate
- GET /api/$version/cdns/name/:name/dnsseckeys/delete
- GET /internal/api/$version/cdns/dnsseckeys/refresh (deprecated?)
- POST /api/1.4/cdns/{name}/dnsseckeys/ksk/generate
- GET /api/1.3/deliveryservices/{xmlID}/urisignkeys
- POST /api/1.3/deliveryservices/{xmlID}/urisignkeys
- PUT /api/1.3/deliveryservices/{xmlID}/urisignkeys
- DELETE /api/1.3/deliveryservices/{xmlID}/urisignkeys
- the various snapshot APIs (certs from deleted delivery services are deleted from Riak)
- the deliveryservices PUT and POST endpoints (creating/updating dnsseckeys and updating sslkeys)

The above endpoints that are not Riak-specific will be updated to use the
`SecureDB` interface, of which the concrete implementation will handle reading
from and writing to the secure data store backend that has been configured for
Traffic Ops. The format of the API requests and responses should remain exactly
the same as they are currently, so from a TO API client perspective there
should be no change. The only difference will be which backend TO is using as
its secure data store.

#### Client Impact

n/a

#### Data Model / Database Impact

The TO internal data model shouldn't require much change, but new structs may
be required for marshalling/unmarshalling between TO and any new `SecureDB`
backends. The lib/go-tc structs should be unaffected by this change.

This change should not require any new changes to the database schema, but it
might be required to seed new server/profile types for adding new servers into
TO that correspond to a `SecureDB` backend, similar to the server type `RIAK`
and profile type `RIAK_PROFILE` for the existing Riak backend.

### ORT Impact

n/a

### Traffic Monitor Impact

n/a

### Traffic Router Impact

n/a

### Traffic Stats Impact

n/a

### Traffic Vault Impact

The existing Traffic Vault Riak backend will remain the default `SecureDB`
backend if no backend has been chosen in the TO configuration, and the existing
format of Riak requests and responses should not change due to this blueprint.

Some new Traffic Vault backends may be implemented as part of this blueprint,
which may or may not include simple in-memory or file-based implementations.

No *new* data requirements will be added to the system as part of this change,
and existing data in Riak will be unchanged.

### Documentation Impact

Any new `SecureDB`/Traffic Vault backends should be documented along with their
required configuration (or lack thereof). Existing Riak-related documentation
should be reorganized into backend-specific places. E.g. Traffic Vault should
have an overview, with a listing of supported backends (including Riak). Each
supported backend would then have its own page of documentation describing
setup, configuration, etc. of that specific backend.

### Testing Impact

Once this blueprint is implemented, TO API tests that would *normally* depend
on Riak could be tested using the simple in-memory or file-based `SecureDB`
backend, allowing for tests of those endpoints to be more easily added and run.

At the same time, we should consider adding TO API testing support with an
actual Riak backend, so that the TO API tests can be run against a running Riak
installation where possible.

In addition to adding TO API tests, we should implement parity tests where a
client makes the same set of requests to two different TO instances and
verifies the responses are the same. One TO instance should be configured to
use the Riak backend, and the other should be configured to use a different
backend.

### Performance Impact

n/a

### Security Impact

The new refactored Riak implementation of the `SecureDB` interface should not
introduce any changes in the traffic between TO and Riak -- traffic that is
encrypted today will remain encrypted after this blueprint is implemented. Any
new simple in-memory and/or file-based `SecureDB` backends should be considered
insecure and only used for development and testing purposes. Production
`SecureDB` backends should continue to be Riak until a sufficient replacement
is supported.

### Upgrade Impact

Traffic Ops should be able to be upgraded without any new required
configuration changes. By default (if no specific `SecureDB` backend has been
specified in the configuration), Traffic Ops will assume that Riak is the
`SecureDB` backend. If a specific `SecureDB` backend has not been specified and
Riak is not enabled, the API endpoints that use the `SecureDB` will return an
error similar to how they return an error today when Riak is not enabled.

Once Traffic Ops has been upgraded to a version that supports new `SecureDB`
backends, a Traffic Ops administrator should continue running the Riak
`SecureDB` backend until a sufficient replacement becomes supported, and they
might want to explicitly configure `riak` as the specified `SecureDB` backend
until then.

### Operations Impact

By default, operators should be able to ignore the new `SecureDB` configuration
and continue using their existing Riak configuration. Once support for a Riak
replacement has been implemented as a `SecureDB` backend, operators should be
provided with instructions on how to configure and transition to the new
`SecureDB` backend. However, providing a Riak replacement is out of the scope
of this blueprint, so those instructions will not be required until then.

### Developer Impact

With the addition of a simple in-memory and/or file-based `SecureDB` backend,
developers will more easily be able to develop and test TO API endpoints that
require a `SecureDB` backend. Currently, Riak is the only supported `SecureDB`
backend, and configuring Riak and running it locally for a development
environment is not trivial. By being able to develop and test against a
`SecureDB` backend that comes for free with Traffic Ops, developers can focus
on the business domain logic separately from the integration with the
`SecureDB` backend. Once the business domain logic is completed, developers can
test their implementation against a Production-ready backend like Riak.

Developers should be made aware of the new `SecureDB` interface and the fact
that there should be a clean separation between the TO API implementation of
the business logic and the integration with a particular `SecureDB` backend.
Simply put, the business logic should only depend on the `SecureDB` interface,
never on a concrete implementation of that interface (such as Riak). This
interface and its associated methods should be well documented in the code
itself, and a `README` about the `SecureDB` interface might be prudent as well,
so that developers will have an easier time implementing support for new
`SecureDB` backends (such as HashiCorp Vault).

## Alternatives

Some alternatives might include:
- rather than abstract the `SecureDB` implementations behind an interface and
  configuring which one to use, just swap in support for a different backend
  - by being more direct, might be easier to implement
  - doesn't fix the issue of being able to easily run/test TO API endpoints
    that require a secure data store without having to run a complex data store
  - an upgrade to the latest version of TO would require swapping in the new
    data store immediately
  - swapping in data store N+1 would remain as difficult as swapping in data
    store N was, instead of making it simpler to add new data stores

I think it's important that we abstract away the concrete `SecureDB`
implementations behind a well-defined interface so that we have more freedom to
swap in various data store technologies instead of tying our fate to one
particular data store, especially when there are so many available options.

## Dependencies

n/a

## References

n/a
