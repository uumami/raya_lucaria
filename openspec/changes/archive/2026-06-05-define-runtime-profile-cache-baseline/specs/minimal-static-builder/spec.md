## ADDED Requirements

### Requirement: Static runtime metadata output
The minimal static builder SHALL emit runtime and execution metadata as generated artifact data without executing code or notebooks.

#### Scenario: Runtime profile metadata emitted
- **WHEN** a course declares valid runtime profiles
- **THEN** the builder MUST emit manifest-declared runtime metadata derived from `runtime/profiles.yaml` and related root runtime files

#### Scenario: Execution plan metadata emitted
- **WHEN** a course has code or notebook references with execution policy metadata
- **THEN** the builder MUST emit manifest-declared execution plan metadata with target IDs, policy, runtime profile when declared, and status `not-executed`

#### Scenario: Cache metadata emitted
- **WHEN** executable targets declare policy `cache`, `always`, or `frozen`
- **THEN** the builder MUST emit manifest-declared cache-key metadata without executing targets or refreshing outputs

#### Scenario: Static pages preserved
- **WHEN** runtime metadata is present
- **THEN** generated pages, deployment-neutral links, reference panels, assets, navigation, indexes, and static read paths MUST remain usable without runtime support

### Requirement: Runtime metadata indexes
The minimal static builder SHALL keep runtime, execution-plan, and cache metadata machine-readable and manifest-centered.

#### Scenario: Metadata data files validate
- **WHEN** the builder writes runtime, execution-plan, or cache metadata files
- **THEN** those files MUST pass the accepted artifact data validators during build

#### Scenario: No runtime metadata omitted or empty
- **WHEN** a course has no runtime profiles and no executable policy metadata beyond the Phase 2 default
- **THEN** the artifact MUST either omit runtime/cache metadata from the manifest or emit empty valid metadata files consistently
