# Spec Refactoring Summary - Phase-Based Approach

**Date**: 2026-01-26  
**Reason**: Focus on AAP instance setup first, defer other parts to later phases

## What Changed

The original comprehensive spec (`spec.md`) has been refactored into **4 focused phases**:

### ✅ Phase 1: AAP Instance Setup (CURRENT FOCUS)
- **Spec**: [spec-phase1-aap-setup.md](spec-phase1-aap-setup.md)
- **Plan**: [plan-phase1-aap-setup.md](plan-phase1-aap-setup.md)
- **Tasks**: [tasks-phase1-aap-setup.md](tasks-phase1-aap-setup.md)
- **Goal**: Get AAP 2.5 or 2.6 running using aap-dev
- **Deliverables**:
  - `tests/integration/setup_aap.sh` - Start AAP
  - `tests/integration/cleanup_aap.sh` - Stop AAP
  - `tests/integration/README-phase1.md` - Documentation
- **Estimated Effort**: 4-6 hours
- **Status**: Ready to implement

### 📋 Phase 2: AAP Test Data Creation (FUTURE)
- **Spec**: [spec-phase2-aap-data.md](spec-phase2-aap-data.md)
- **Goal**: Populate AAP with test organizations, projects, jobs, users
- **Depends On**: Phase 1 complete
- **Status**: Stub created, to be detailed later

### 📋 Phase 3: Container Setup & Data Sync (FUTURE)
- **Spec**: [spec-phase3-containers.md](spec-phase3-containers.md)
- **Goal**: Start dashboard containers (postgres, redis, web, task) and sync data
- **Depends On**: Phase 1 and 2 complete
- **Status**: Stub created, to be detailed later

### 📋 Phase 4: Database Validation (FUTURE)
- **Spec**: [spec-phase4-validation.md](spec-phase4-validation.md)
- **Goal**: Validate exact database object counts using pytest
- **Depends On**: Phase 1, 2, and 3 complete
- **Status**: Stub created, to be detailed later

## Why This Refactoring?

**Original Problem**: The full spec was comprehensive but trying to do everything at once:
- AAP setup
- Test data creation
- Container orchestration
- Data synchronization
- Database validation
- GitHub Actions integration

**Solution**: Break into phases, focus on **foundation first** (AAP setup).

**Benefits**:
1. ✅ Clear, achievable focus (AAP setup in 4-6 hours)
2. ✅ Each phase can be tested independently
3. ✅ Unblocks development - can work on later phases while Phase 1 is being tested
4. ✅ Easier to maintain and understand
5. ✅ Reduces risk of incomplete implementation

## File Organization

```
specs/001-container-image-test/
├── REFACTORING-SUMMARY.md          # This file
│
├── spec-phase1-aap-setup.md        # Phase 1: AAP Setup (CURRENT)
├── plan-phase1-aap-setup.md        # Phase 1: Plan
├── tasks-phase1-aap-setup.md       # Phase 1: Tasks (40 tasks)
│
├── spec-phase2-aap-data.md         # Phase 2: Test Data (stub)
├── spec-phase3-containers.md       # Phase 3: Containers (stub)
├── spec-phase4-validation.md       # Phase 4: Validation (stub)
│
├── spec.md                         # Original comprehensive spec (reference)
├── plan.md                         # Original comprehensive plan (reference)
├── tasks.md                        # Original comprehensive tasks (reference)
├── research.md                     # Research findings
├── data-model.md                   # Data model (for Phase 4)
├── quickstart.md                   # Quick reference (to be updated per phase)
│
└── contracts/                      # Validation contracts (for Phase 4)
    └── validation-contract.md
```

## What to Do Next

### Immediate (Phase 1):
1. Review [spec-phase1-aap-setup.md](spec-phase1-aap-setup.md)
2. Review [tasks-phase1-aap-setup.md](tasks-phase1-aap-setup.md)
3. Start implementing AAP setup script
4. Test AAP 2.5 and 2.6 startup
5. Document usage

### After Phase 1 Complete:
1. Detail spec-phase2-aap-data.md (test data creation)
2. Create plan-phase2-aap-data.md
3. Create tasks-phase2-aap-data.md
4. Implement Phase 2

### Future Phases:
Follow same pattern for Phase 3 and Phase 4.

## Original Documents

The original comprehensive documents remain available for reference:
- [spec.md](spec.md) - Full feature specification
- [plan.md](plan.md) - Full implementation plan
- [tasks.md](tasks.md) - Full task breakdown (404 lines)

These provide the complete vision but were too large to implement in one go.

## Questions?

- **Q**: Should I delete the original spec.md/plan.md/tasks.md?
  - **A**: No, keep them as reference. They show the complete vision.

- **Q**: When will phases 2-4 be detailed?
  - **A**: After each previous phase is tested and working.

- **Q**: Can phases run in parallel?
  - **A**: No, they have dependencies. Must complete in sequence.

- **Q**: How long will all phases take?
  - **A**: Estimated 15-20 hours total across all 4 phases.

## Summary

**Before**: One large spec trying to do everything  
**After**: 4 focused phases, starting with AAP setup only  
**Benefit**: Clear, achievable goals with steady progress  

**Current Focus**: [spec-phase1-aap-setup.md](spec-phase1-aap-setup.md) - Get AAP running! 🚀
