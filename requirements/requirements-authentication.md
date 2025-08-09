### Functional Requirements

**1. User Authentication & Authorization**
* **Dual Login:** The application's landing page must present two clear and separate login options: "Login with Keycloak" and "Login with Google".
* **New User Onboarding:** Upon a new user's first successful login via either Keycloak or Google, the system must automatically create a new user account in its internal database.
* **Site-User Mapping:** After a user authenticates, the system must associate their account with a pre-existing "site" or "tenant" within the database.
* **Domain Restriction:** The system must validate that the user's email address belongs to a pre-approved list of domains (e.g., `@gmail.com` for Google, or a specific corporate domain for Keycloak). Unapproved domains should be rejected with an appropriate error message.
* **User Provisioning:** The user's account must be provisioned with a default role and access to at least one site before they can proceed.

**2. Multi-Tenancy & User Experience**
* **Site Selection Screen:** If a user is a member of more than one site, the application must display a clear and user-friendly interface for them to select their desired site immediately after a successful login.
* **Direct Access:** If a user is a member of only a single site, they should be automatically and seamlessly redirected to that site's dashboard without being prompted to make a selection.
* **No Access Notification:** If an authenticated user is not mapped to any site, the application must display a clear message stating they do not have access and should contact an administrator. This is crucial for preventing a confusing user experience.

**3. Application Security**
* **Protected Resources:** All data and application functions must be protected from unauthorized access. Only authenticated and authorized users should be able to make API calls to the backend.
* **Tenant Data Isolation:** The backend must guarantee that a user cannot view, edit, or interact with data belonging to a site they are not currently a member of. This isolation must be enforced on every API request.
* **Role-Based Permissions:** The system must enforce permissions based on the user's role (e.g., "admin," "member") within their current site. An "admin" can perform actions a "member" cannot.

---

### Technical Requirements

**1. Front-End (React Application)**
* **Authentication Libraries:**
    * Integrate a Google Sign-In library to handle the Google OAuth flow and retrieve the ID token.
    * Integrate a Keycloak adapter library (e.g., `@react-keycloak/web`) to manage the Keycloak authentication lifecycle, token validation, and state.
* **State Management:** The application state must track the user's authentication status, the current user details, and the ID of the selected site.
* **Secure API Calls:**
    * The front-end must send an application-issued JWT in the `Authorization: Bearer <token>` header for all authenticated requests.
    * A custom `X-Current-Site-ID` header must be included in every API call to inform the backend of the user's active site context.

**2. Back-End (FastAPI Application)**
* **Framework and Dependencies:**
    * Use FastAPI to build the API endpoints.
    * Utilize a library for validating Google ID tokens (e.g., `google-auth`).
    * Implement a Keycloak middleware (e.g., `fastapi-keycloak-middleware`) to validate incoming Keycloak JWTs.
* **Core Authentication Endpoints:**
    * `POST /auth/google`: Accepts the Google ID token. It must validate the token, extract the email and Google ID, create/retrieve the user from the database, determine their site memberships, generate a new application JWT containing user and site information, and return it.
    * A similar internal flow for Keycloak logins.
* **Database Schema:**
    * `users` table: Columns for `id`, `email`, `keycloak_id`, and `google_id`.
    * `sites` table: Columns for `id`, `name`, and other site-specific data.
    * `site_members` table: A join table with foreign keys to `users.id` and `sites.id`, and a column for the user's `role` within that site.
* **Middleware and Security:**
    * Implement a custom security dependency that runs on every protected route.
    * This dependency must: 1) validate the application JWT, 2) check the `X-Current-Site-ID` header, 3) verify that the authenticated user is a member of that site and has the necessary permissions.
    * Use environment variables to store all secrets, including the JWT signing key and database credentials.
