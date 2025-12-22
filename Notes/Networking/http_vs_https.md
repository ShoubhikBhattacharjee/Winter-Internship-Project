# Web Protocols: HTTP vs. HTTPS

## HTTP (Hypertext Transfer Protocol)
HTTP is the foundation of data exchange on the web. It is an application layer protocol that operates on a client-server model.
- **Security:** Data is sent as unencrypted plain text. This makes it susceptible to "Man-in-the-Middle" (MITM) attacks where hackers can intercept and read sensitive info.
- **Port:** Uses **Port 80** by default.
- **Use Case:** Primarily used for general browsing of public information where security is not a high priority.

## HTTPS (Hypertext Transfer Protocol Secure)
HTTPS is the secure version of HTTP. It uses cryptographic protocols to protect data in transit.
- **Security:** Uses **SSL/TLS** (Secure Sockets Layer / Transport Layer Security) to encrypt data, ensuring confidentiality, integrity, and authentication.
- **Port:** Uses **Port 443** by default.
- **Verification:** Requires an SSL certificate from a trusted Certificate Authority (CA) to verify the server's identity.

## Key Differences at a Glance
| Feature | HTTP | HTTPS |
| :--- | :--- | :--- |
| **Security** | Insecure (Plain Text) | Secure (Encrypted) |
| **Default Port** | 80 | 443 |
| **OSI Layer** | Application Layer | Transport Layer (via TLS) |
| **Browser Indicator** | "Not Secure" warning | Padlock Icon |