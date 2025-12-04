# Comprehensive Data Ingestion Function Documentation

Generated: 2025-12-04T11:19:46.301113

## Summary

- Total Classes: 3
- Total Methods: 16
- Total Functions: 6
- Total Documented: 22

## DataIngestionManager

Comprehensive data ingestion manager

### __init__

**Signature:** `__init__(self: Any, config: <class 'comprehensive_data_ingestion.IngestionConfig'>) -> Any`

**Description:** No documentation available

### generate_report

**Signature:** `generate_report(self: Any, results: typing.List[comprehensive_data_ingestion.IngestionResult]) -> typing.Dict[str, typing.Any]`

**Description:** Generate comprehensive ingestion report

### ingest_congress_data

**Signature:** `ingest_congress_data(self: Any, congress: <class 'int'>, bill_type: <class 'str'>) -> <class 'comprehensive_data_ingestion.IngestionResult'>`

**Description:** Ingest Congress.gov data

### ingest_govinfo_data

**Signature:** `ingest_govinfo_data(self: Any, collection: <class 'str'>, year: <class 'int'>) -> <class 'comprehensive_data_ingestion.IngestionResult'>`

**Description:** Ingest GovInfo data

### ingest_openstates_data

**Signature:** `ingest_openstates_data(self: Any, state: <class 'str'>, session: <class 'str'>) -> <class 'comprehensive_data_ingestion.IngestionResult'>`

**Description:** Ingest OpenStates data

### run_comprehensive_ingestion

**Signature:** `run_comprehensive_ingestion(self: Any) -> typing.List[comprehensive_data_ingestion.IngestionResult]`

**Description:** Run comprehensive ingestion of all data sources

### save_report

**Signature:** `save_report(self: Any, report: typing.Dict[str, typing.Any], format: <class 'str'>) -> <class 'bool'>`

**Description:** Save ingestion report

## IngestionConfig

Configuration for data ingestion

### __eq__

**Signature:** `__eq__(self: Any, other: Any) -> Any`

**Description:** No documentation available

### __init__

**Signature:** `__init__(self: Any, congress_api_key: <class 'str'>, govinfo_api_key: <class 'str'>, openstates_api_key: <class 'str'>, database_url: <class 'str'>, data_directory: <class 'str'>, log_level: <class 'str'>, max_workers: <class 'int'>, batch_size: <class 'int'>, timeout: <class 'int'>, max_retries: <class 'int'>) -> None`

**Description:** No documentation available

### __repr__

**Signature:** `__repr__(self: Any) -> Any`

**Description:** No documentation available

## IngestionResult

Result of ingestion operation

### __eq__

**Signature:** `__eq__(self: Any, other: Any) -> Any`

**Description:** No documentation available

### __init__

**Signature:** `__init__(self: Any, source: <class 'str'>, records_processed: <class 'int'>, records_successful: <class 'int'>, records_failed: <class 'int'>, start_time: <class 'float'>, end_time: <class 'float'>, errors: typing.List[str]) -> None`

**Description:** No documentation available

### __post_init__

**Signature:** `__post_init__(self: Any) -> Any`

**Description:** No documentation available

### __repr__

**Signature:** `__repr__(self: Any) -> Any`

**Description:** No documentation available

### duration

**Signature:** `duration(self: Any) -> <class 'float'>`

**Description:** Calculate duration of ingestion

### success_rate

**Signature:** `success_rate(self: Any) -> <class 'float'>`

**Description:** Calculate success rate

## Module Functions

### as_completed

**Signature:** `as_completed(fs: Any, timeout: Any) -> Any`

**Description:** An iterator over the given futures that yields each as it completes.

**Details:**

- Args:
- fs: The sequence of Futures (possibly created by different Executors) to
- iterate over.
- timeout: The maximum number of seconds to wait. If None, then there
- is no limit on the wait time.
- Returns:
- An iterator that yields the given Futures as they complete (finished or
- cancelled). If any given Futures are duplicated, they will be returned
- once.
- Raises:
- TimeoutError: If the entire result iterator could not be generated
- before the given timeout.

### dataclass

**Signature:** `dataclass(cls: Any, init: Any, repr: Any, eq: Any, order: Any, unsafe_hash: Any, frozen: Any, match_args: Any, kw_only: Any, slots: Any, weakref_slot: Any) -> Any`

**Description:** Add dunder methods based on the fields defined in the class.

**Details:**

- Examines PEP 526 __annotations__ to determine fields.
- If init is true, an __init__() method is added to the class. If repr
- is true, a __repr__() method is added. If order is true, rich
- comparison dunder methods are added. If unsafe_hash is true, a
- __hash__() method is added. If frozen is true, fields may not be
- assigned to after instance creation. If match_args is true, the
- __match_args__ tuple is added. If kw_only is true, then by default
- all fields are keyword-only. If slots is true, a new class with a
- __slots__ attribute is returned.

### main

**Signature:** `main() -> Any`

**Description:** Main function

### urljoin

**Signature:** `urljoin(base: Any, url: Any, allow_fragments: Any) -> Any`

**Description:** Join a base URL and a possibly relative URL to form an absolute

**Details:**

- interpretation of the latter.

### urlparse

**Signature:** `urlparse(url: Any, scheme: Any, allow_fragments: Any) -> Any`

**Description:** Parse a URL into 6 components:

**Details:**

- <scheme>://<netloc>/<path>;<params>?<query>#<fragment>
- The result is a named 6-tuple with fields corresponding to the
- above. It is either a ParseResult or ParseResultBytes object,
- depending on the type of the url parameter.
- The username, password, hostname, and port sub-components of netloc
- can also be accessed as attributes of the returned object.
- The scheme argument provides the default value of the scheme
- component when no scheme is found in url.
- If allow_fragments is False, no attempt is made to separate the
- fragment component from the previous component, which can be either
- path or query.
- Note that % escapes are not expanded.

### wraps

**Signature:** `wraps(wrapped: Any, assigned: Any, updated: Any) -> Any`

**Description:** Decorator factory to apply update_wrapper() to a wrapper function

**Details:**

- Returns a decorator that invokes update_wrapper() with the decorated
- function as the wrapper argument and the arguments to wraps() as the
- remaining arguments. Default arguments are as for update_wrapper().
- This is a convenience function to simplify applying partial() to
- update_wrapper().

