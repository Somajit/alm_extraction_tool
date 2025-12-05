# MongoDB Collections Reference

## Overview
ReleaseCraft uses 19 MongoDB collections organized into different functional groups.

## Complete Collection List

### 1. Authentication & User Management (2 collections)
| Collection | Purpose | Created By |
|------------|---------|------------|
| `users` | Basic user accounts | Manual registration or sample data script |
| `user_credentials` | ALM server credentials and active sessions | ALM authentication API |

### 2. Sample/Local Data (4 collections)
| Collection | Purpose | Created By |
|------------|---------|------------|
| `domains` | Local domain list (for sample/test data) | Sample data initialization script |
| `projects` | Local project list (for sample/test data) | Sample data initialization script |
| `tree_cache` | Cached tree structure (TestPlan/TestLab hierarchy) | Sample data or tree loading |
| `defects` | Local defect list (for sample/test data) | Sample data initialization script |

### 3. ALM Extracted Data (4 collections)
| Collection | Purpose | Created By |
|------------|---------|------------|
| `domains_extracted` | Domains fetched from ALM server | ALM domain extraction API |
| `projects_extracted` | Projects fetched from ALM server | ALM project extraction API |
| `testplan_folders` | Test plan folder hierarchy from ALM | TestPlan extraction |
| `defects_extracted` | Defects fetched from ALM server | Defect extraction API |

### 4. Entity & Attachment Storage (4 collections)
| Collection | Purpose | Created By |
|------------|---------|------------|
| `entities` | Generic storage for all ALM entities (folders, tests, releases, cycles, testsets, testruns, defects) | MongoService.insert_entity() |
| `attachments` | Attachment metadata (filename, size, type) for all entity types | MongoService.insert_attachment() |
| `attachment_files` | Binary attachment file content for all entity types | MongoService.insert_attachment_file() |
| `attachment_cache` | Cached attachment downloads from ALM server | Attachment download/cache API |

### 5. Detailed Extraction Results (5 collections)
| Collection | Purpose | Created By |
|------------|---------|------------|
| `testplan_test_details` | Detailed test case information | Test details extraction API |
| `testplan_extraction_results` | TestPlan extraction job status and results | TestPlan recursive extraction |
| `testlab_testset_details` | Detailed test set information | TestLab extraction API |
| `testlab_extraction_results` | TestLab extraction job status and results | TestLab recursive extraction |
| `defect_details` | Detailed defect information | Defect details API |

## Collection Usage Patterns

### During Deployment
**After fresh deployment**: All collections have 0 documents
- No automatic data initialization
- Database is completely empty

### After Sample Data Initialization
**Running `initialize-sample-data.bat` creates**:
- `users`: 1 document (admin/admin123)
- `domains`: 2 documents (DomainA, DomainB)
- `projects`: 3 documents (Project1, Project2, ProjectX)
- `tree_cache`: 2 documents (test plan and test lab trees)
- `defects`: 2 documents (sample defects)
- **Total**: 5 collections, 10 documents

### During ALM Operations

#### Login to ALM
- Creates/updates `user_credentials` with session token

#### Fetch Domains
- Populates `domains_extracted` with domains from ALM server
- One document per domain per username

#### Fetch Projects
- Populates `projects_extracted` with projects from ALM server
- One document per project per username per domain

#### Extract TestPlan Folder
- Creates documents in `testplan_folders` for folder metadata
- Creates documents in `entities` for each folder, subfolder, and test
- Creates documents in `attachments` and `attachment_files` for attachments
- Creates document in `testplan_extraction_results` to track extraction status

#### Extract TestLab Release/Cycle
- Creates documents in `entities` for releases, cycles, testsets, and testruns
- Creates documents in `attachments` and `attachment_files` for attachments
- Creates document in `testlab_extraction_results` to track extraction status

#### Extract Defects
- Populates `defects_extracted` with defect list
- Creates documents in `entities` for each defect
- Creates documents in `defect_details` for detailed defect info

#### Get Details (Test/TestSet/Defect)
- Queries respective detail collections: `testplan_test_details`, `testlab_testset_details`, `defect_details`
- Creates/updates documents with detailed information

## Statistics Script

The `show-detailed-mongo-stats.bat` script checks all 19 collections and displays:
- Database name and overall statistics
- Document count for each collection
- Total data and storage size

**Example output after sample data**:
```
Database: releasecraftdb
Collections: 5
Total Documents: 10
Data Size: 0.02 MB

Collection Details:
users: 1 documents
domains: 2 documents
projects: 3 documents
tree_cache: 2 documents
defects: 2 documents
user_credentials: 0 documents
domains_extracted: 0 documents
projects_extracted: 0 documents
testplan_folders: 0 documents
defects_extracted: 0 documents
entities: 0 documents
attachments: 0 documents
attachment_files: 0 documents
attachment_cache: 0 documents
testplan_test_details: 0 documents
testplan_extraction_results: 0 documents
testlab_testset_details: 0 documents
testlab_extraction_results: 0 documents
defect_details: 0 documents
```

## Important Notes

1. **No automatic initialization**: Deployment does NOT create any collections or documents
2. **Sample data is optional**: Run `initialize-sample-data.bat` only if you want test data
3. **Real data comes from ALM**: Most collections are populated when extracting from ALM server
4. **Separation of concerns**:
   - `users`, `domains`, `projects`, `tree_cache`, `defects` = Local/sample data
   - `*_extracted` collections = Data fetched/extracted from ALM server (domains, projects, defects)
   - `testplan_*` and `testlab_*` collections = TestPlan and TestLab specific data
   - `entities`, `attachments`, `attachment_files` = Generic storage for all ALM entity types
   - `*_details` collections = Detailed information for specific entities
   - `*_results` collections = Extraction job tracking and status
   - `attachment_cache` = Downloaded attachment cache from ALM server

5. **Entity storage**: The `entities` collection is a generic store used by MongoService for all entity types (folders, tests, releases, cycles, testsets, testruns, defects with attachments)
