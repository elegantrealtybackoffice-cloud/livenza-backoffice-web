# Livenza Back Office Web 1.4.9

## Chatbot close control

- Added a prominent cross icon to the chatbot header.
- The close control stays above the scrolling conversation, including after long chats.
- Closing the chatbot returns keyboard focus to the Ask Livenza launcher.
- The Escape key now closes an open chat.
- Static asset cache version and `/version` were updated to Web 1.4.9.

## Food partner website reliability

- Replaced the unreliable embedded iframe with a secure partner-portal launchpad.
- Added Open in New Tab, Open in This Tab and Copy Link actions.
- Updated the built-in Swiggy and Zomato restaurant-partner URLs.
- Existing rows are updated only when they still contain an old built-in URL; custom portal URLs remain untouched.
- Partner passwords, OTPs and session data stay entirely on the official partner website.
