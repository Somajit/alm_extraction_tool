# Collection Structure Changes

## New Collection Architecture

### Entity Collections (16 primary + 8 support = 24 total)

#### TestPlan Collections (6)
1. **testplan_folders** - Test plan folder hierarchy
2. **testplan_tests** - Test cases
3. **testplan_test_design_steps** - Test design steps
4. **testplan_folder_attachments** - Folder attachments
5. **testplan_test_attachments** - Test attachments
6. **testplan_test_design_step_attachments** - Design step attachments

#### TestLab Collections (5)
7. **testlab_releases** - Releases
8. **testlab_release_cycles** - Release cycles
9. **testlab_testsets** - Test sets
10. **testlab_testruns** - Test runs
11. **testlab_testset_attachments** - Test set attachments

#### Defect Collections (2)
12. **defects** - Defects
13. **defect_attachments** - Defect attachments

#### Core Collections (3)
14. **users** - Application users
15. **domains** - Domains
16. **projects** - Projects

#### Support Collections (8)
17. **user_credentials** - ALM credentials and sessions
18. **tree_cache** - Cached tree structures
19. **attachment_cache** - Cached attachment downloads
20. **testplan_test_details** - Detailed test info (temporary storage)
21. **testplan_extraction_results** - Extraction job tracking
22. **testlab_testset_details** - Detailed testset info (temporary storage)
23. **testlab_extraction_results** - TestLab extraction tracking
24. **defect_details** - Detailed defect info (temporary storage)

## Mandatory Fields for All Entity Collections

Every entity collection MUST have these fields:
- **user**: Username (who extracted/created the data)
- **id**: Entity unique identifier
- **name**: Entity name/title
- **parent_id**: Parent entity ID (for hierarchy)

Additional fields are defined in `ALMConfig.ENTITY_FIELD_CONFIG`.

## Field Configuration Structure

Each collection has field configuration with:
- **field**: Field name in MongoDB
- **alias**: Display name for UI/exports
- **sequence**: Display order (ascending)
- **display**: Boolean - show in exports/details?

## Display Rules

1. **Show Details / Context Menu**: Display only fields where `display=True`, sorted by `sequence`
2. **JSON Export**: Same as above, use `alias` as key names
3. **Excel Export**: Same as above, `alias` becomes column header
4. **MongoDB Storage**: Store ALL fields (regardless of display flag)

## Old vs New Collections

| Old Collection | New Collection(s) | Status |
|---------------|-------------------|--------|
| alm_entities | Split into specific entity collections | REMOVED |
| alm_attachments | Split by parent type (6 attachment collections) | REMOVED |
| alm_attachment_files | Merged into attachment collections | REMOVED |
| alm_domains | domains | RENAMED |
| alm_projects | projects | RENAMED |
| alm_test_folders | testplan_folders | RENAMED |
| alm_defects | defects | RENAMED |
| attachments | attachment_cache | RENAMED |
| tree | tree_cache | RENAMED |
| test_details | testplan_test_details | RENAMED |
| extraction_results | testplan_extraction_results | RENAMED |
| testset_details | testlab_testset_details | RENAMED |

## Benefits

1. **Clarity**: Collection names immediately indicate what they store
2. **Separation**: Each entity type has its own collection
3. **Attachments**: Separate attachment collections by parent type
4. **Consistency**: All collections follow same naming pattern
5. **Flexibility**: Field display controlled by configuration
6. **Maintainability**: Easy to add new fields or entities
