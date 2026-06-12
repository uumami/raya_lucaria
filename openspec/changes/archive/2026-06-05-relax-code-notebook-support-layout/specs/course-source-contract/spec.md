## MODIFIED Requirements

### Requirement: Ordered content tree
Source courses SHALL use ordered source-tree conventions for rendered material while allowing private, draft, official, asset, partial, and source support material to remain unrendered.

#### Scenario: Ordered content entries validated
- **WHEN** validation scans the configured authored source root
- **THEN** it MUST classify rendered numeric entries, rendered appendix entries, section landing pages, private paths, draft paths, `_official/`, `_reviewed/`, `_assets/`, partial paths, extension-classified `.py` and `.ipynb` source support files, support-only directories, and invalid unordered files

#### Scenario: Invalid ordered tree fails
- **WHEN** validation finds duplicate normalized order values, mixed main prefix widths in one sibling set, missing section landing pages, duplicate clean slugs, or unordered published Markdown files
- **THEN** validation MUST fail with actionable diagnostics

#### Scenario: Support-only directory does not create order
- **WHEN** an ordinary directory under the authored source root contains source support files but no rendered Markdown files
- **THEN** validation MUST NOT require that directory to use an order prefix or section landing page solely because of those source support files

### Requirement: Unified authored source tree
The authored source tree SHALL organize rendered pages and non-rendered support material under the learning quanta they belong to.

#### Scenario: Support directories do not render
- **WHEN** `_official/`, `_reviewed/`, `_assets/`, `_drafts/`, `drafts/`, or `_partials/` exists under the authored source root
- **THEN** validation MUST treat those directories as private source support material and MUST NOT include them in rendered navigation, generated local indexes, or master indexes

#### Scenario: Quantum support uses directory page
- **WHEN** a learning quantum owns `_official/` or `_assets/` support material
- **THEN** that quantum MUST be represented as a rendered directory with a normalized zero index page such as `0_index.md`

#### Scenario: File page remains valid without support
- **WHEN** a rendered file page such as `1_topic.md` has no child support directories
- **THEN** validation MUST continue to accept it as a rendered page

#### Scenario: Extension support does not render
- **WHEN** validation scans `.py` or `.ipynb` files under the authored source root
- **THEN** those files MUST NOT become rendered navigation entries, generated index entries, or page quanta

## ADDED Requirements

### Requirement: Extension-classified code and notebook source support
The source course contract SHALL support linked `.py` and `.ipynb` files as authored source support material owned by a learning quantum or accepted ancestor without requiring special directory names.

#### Scenario: Linked script support
- **WHEN** a rendered page links to an existing `.py` file under its own learning quantum or an accepted ancestor quantum
- **THEN** validation MUST treat the target as code source support regardless of the ordinary folder name that contains it

#### Scenario: Linked notebook support
- **WHEN** a rendered page links to an existing `.ipynb` file under its own learning quantum or an accepted ancestor quantum
- **THEN** validation MUST treat the target as notebook source support regardless of the ordinary folder name that contains it

#### Scenario: Optional author folder names
- **WHEN** authors choose folder names such as `code/`, `notebooks/`, `scripts/`, `helpers/`, or `labs/` under a learning quantum
- **THEN** validation MUST treat those names as ordinary organization choices rather than required or reserved source support roots

#### Scenario: Support owner has index page
- **WHEN** source support files belong to a directory learning quantum
- **THEN** that quantum MUST be represented by a normalized zero index page such as `0_index.md`

#### Scenario: Root source code fields unsupported
- **WHEN** a course declares a root authored `code` or `notebooks` configuration field
- **THEN** validation MUST fail or ignore it according to the source-course contract and tell authors to keep authored support material under `course/`

## REMOVED Requirements

### Requirement: Code and notebook support directories
**Reason**: Mandatory `code/` and `notebooks/` support roots are replaced by extension-classified linked support files so authors can organize scripts and notebooks naturally under the learning quanta they serve.

**Migration**: Existing `code/` and `notebooks/` paths may remain as ordinary author folder names if rendered Markdown links still point to them. Implementations MUST stop treating those names as reserved support roots.
