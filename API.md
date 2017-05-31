# Open Desktop Ratings Service API

## Ratings statistics

    GET /ratings

### Response

    [
        "app.desktop": {  // Appstream ID
            "star0": 0,   // Number of zero star ratings
            "star1": 0,   // Number of one star ratings
            "star2": 0,   // Number of two star ratings
            "star3": 1,   // Number of three star ratings
            "star4": 4,   // Number of four star ratings
            "star5": 27,  // Number of five star ratings
            "total": 32   // Total number of ratings
        },
        ...
    ]

## Get ratings for an app

    POST /fetch

### Request

    {
        "user_hash": "da39a3ee5e6b4b0d3255bfef95601890afd80709",  // SHA1 hash from gnome-software[USERNAME:MACHINE-ID], machine-id from /etc/machine-id
        "app_id": "app.desktop",                                  // AppStream ID of app to request
        "locale": "en_US",                                        // Locale in the form ISO 15897 without character set, used to filter out reviews that can't be seen
        "distro": "Fedora",                                       // Distribution name, NAME from /etc/os-release (not currently used)
        "version": "unknown",                                     // Version currently installed or "unknown" (not currently used)
        "limit": 20                                               // Maximum number of reviews to return or 0 for unlimited
    }

### Response

     [
         {
             "app_id": "app.desktop"                                   // AppStream ID of app being reviewed
             "date_created": 1495355183,                               // Date review was created as a Unix UTC count in seconds
             "date_deleted": null,                                     // Date review was deleted or null
             "description: "This app is great!\nLOVE IT!",             // Multiple line description for review
             "distro": "Fedora",                                       // Distro app was reviewed on
             "karma_down": 0,                                          // Number of people who have voted this rating down
             "karma_up": 3,                                            // Number of people who have voted this rating up (optional)
             "locale": "en_US",                                        // Locale of reviewer
             "rating": 100,                                            // Rating from 0-100
             "reported": 0,                                            // Number of times this review was reported as inappropriate
             "review_id": 123,                                         // Unique ID for this review
             "score": 42,                                              // Quality score determined by the server - higher is better
             "summary": "Love",                                        // Single line summary for review
             "user_display": "Joe",                                    // Display name for user
             "user_hash": "da39a3ee5e6b4b0d3255bfef95601890afd80709",  // SHA1 hash for user
             "user_skey": "11f6ad8ec52a2984abaafd7c3b516503785c2072",  // Secret key from server to provide reviews with
             "version": "1.2",                                         // Version of software review was written about
             "vote_id": 1                                              // 1 if the user has already voted on this review (optional)
         },
         ...
     ]

If no reviews exist a dummy response is sent to provide user_skey:

     [
         {
             "app_id": "app.desktop"                                   // AppStream ID of app being reviewed
             "score": 0,                                               // Quality score (always zero)
             "user_hash": "da39a3ee5e6b4b0d3255bfef95601890afd80709",  // SHA1 hash for user
             "user_skey": "11f6ad8ec52a2984abaafd7c3b516503785c2072",  // Secret key from server to provide reviews with
         }
     ]

## Rate an app

    POST /submit

### Request

     {
         "app_id": "app.desktop"                                   // AppStream ID of app being reviewed
         "description: "This app is great!\nLOVE IT!",             // Multiple line description for review
         "distro": "Fedora",                                       // Distro app was reviewed on
         "locale": "en_US",                                        // Locale of reviewer
         "rating": 100,                                            // Rating from 0-100
         "summary": "Love",                                        // Single line summary for review
         "user_display": "Joe",                                    // Display name for user
         "user_hash": "da39a3ee5e6b4b0d3255bfef95601890afd80709",  // SHA1 hash for user
         "user_skey": "11f6ad8ec52a2984abaafd7c3b516503785c2072",  // Secret key returned for this app from /fetch
         "version": "1.2",                                         // Version of software review was written about
     }
