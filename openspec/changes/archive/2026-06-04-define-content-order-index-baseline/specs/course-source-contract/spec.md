## MODIFIED Requirements

### Requirement: Learning quanta
Directories and pages SHALL be treated as learning quanta that can define navigation, graph, study, authority, and export scope.

#### Scenario: Path-derived draft identity
- **WHEN** a draft, private, or non-published page has no explicit quantum metadata
- **THEN** validation MUST derive a candidate quantum identity from `course_id` and content path for diagnostics without treating it as a stable published reference

#### Scenario: Published page stable identity
- **WHEN** a rendered published page or section landing page is validated
- **THEN** it MUST declare a globally unique stable ID through supported frontmatter

#### Scenario: Duplicate explicit quantum identity
- **WHEN** two quanta declare the same explicit stable ID
- **THEN** validation MUST fail and identify both declarations

#### Scenario: Directory quantum from index page
- **WHEN** a rendered source directory participates in navigation
- **THEN** validation MUST treat its normalized zero index page as the metadata and content source for the directory quantum

## ADDED Requirements

### Requirement: Ordered content tree
Source courses SHALL use ordered content tree conventions for rendered material while allowing private, draft, and partial material to remain unrendered.

#### Scenario: Ordered content entries validated
- **WHEN** validation scans the configured content directory
- **THEN** it MUST classify rendered numeric entries, rendered appendix entries, section landing pages, private paths, draft paths, and invalid unordered files

#### Scenario: Invalid ordered tree fails
- **WHEN** validation finds duplicate normalized order values, mixed main prefix widths in one sibling set, missing section landing pages, duplicate clean slugs, or unordered published Markdown files
- **THEN** validation MUST fail with actionable diagnostics

### Requirement: Frontmatter metadata baseline
Course content SHALL use supported YAML frontmatter metadata for stable identity and generated index previews.

#### Scenario: Metadata parsed
- **WHEN** validation scans Markdown content with supported YAML frontmatter
- **THEN** it MUST parse supported metadata fields needed for stable identity, title, navigation label, summary, status, estimated time, tags, prerequisites, and aliases

#### Scenario: Broken metadata fails
- **WHEN** a rendered page declares malformed frontmatter or unsupported values for required metadata fields
- **THEN** validation MUST fail and identify the file and field

### Requirement: Configured hierarchy labels
Course configuration SHALL support optional hierarchy labels for rendered navigation without changing source containment or order.

#### Scenario: Hierarchy labels configured
- **WHEN** `raya.yaml` declares hierarchy labels
- **THEN** validation MUST accept those labels and make them available to build and artifact generation

#### Scenario: Hierarchy labels absent
- **WHEN** `raya.yaml` omits hierarchy labels
- **THEN** validation MUST use default labels and MUST NOT require directory-level metadata to infer hierarchy
