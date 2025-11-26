## Pull Request Checklist
 
**Before submitting this PR, please ensure the following:**
 
- [ ] **Code Quality & Functionality:**
    - [ ] The code adheres to established coding standards and style guides.
    - [ ] All new features or bug fixes are fully implemented and functional.
    - [ ] No unnecessary or commented-out code is present.
    - [ ] Code is well-commented where necessary, explaining complex logic.
    - [ ] Project runs with python manage.py runserver without errors.
    - [ ] Required apps are added in INSTALLED_APPS.
    - [ ] Settings (database, debug, allowed hosts) are appropriate for development (and separated from production if needed).
    - [ ] Validation is handled (either in serializer validate() or field-level validators).
    - [ ] Custom validation errors are clear and user-friendly.
    - [ ] Only necessary HTTP methods are allowed (GET/POST/PUT/PATCH/DELETE).
    - [ ] Proper status codes are returned (200, 201, 400, 404, 401, 403, etc.).
- [ ] **Testing:**
    - [ ] All existing tests pass successfully.
    - [ ] New unit tests are added for new features or bug fixes, if applicable.
    - [ ] Integration tests are updated or added, if applicable.
- [ ] **Security & Error Handling:**
    - [ ] Security implications of the changes have been considered and addressed.
    - [ ] Appropriate error handling is implemented for all potential failure points.

 
**Type of Change:**
 
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
