# Testing JSON Server

## Quick Tests

### 1. Check if Server is Running

```bash
# Check service status (on Synology NAS)
sudo synopkg status Json-Server

# Check if port is listening
netstat -tuln | grep 3000
# or
ss -tuln | grep 3000

# Check process
ps aux | grep json-server
```

### 2. Test with cURL

Replace `YOUR_NAS_IP` with your Synology NAS IP address.

#### Test Root Endpoint (Database overview)
```bash
curl http://YOUR_NAS_IP:3000
```

#### Test Posts Endpoint
```bash
# Get all posts
curl http://YOUR_NAS_IP:3000/posts

# Get post by ID
curl http://YOUR_NAS_IP:3000/posts/1

# Pretty print JSON
curl http://YOUR_NAS_IP:3000/posts | python3 -m json.tool
```

#### Test Comments Endpoint
```bash
curl http://YOUR_NAS_IP:3000/comments
curl http://YOUR_NAS_IP:3000/comments/1
```

#### Test Profile Endpoint
```bash
curl http://YOUR_NAS_IP:3000/profile
```

#### Test Filtering (json-server feature)
```bash
# Get posts by author
curl "http://YOUR_NAS_IP:3000/posts?author=John"

# Get comments for a specific post
curl "http://YOUR_NAS_IP:3000/comments?postId=1"
```

#### Test POST (Create new resource)
```bash
curl -X POST http://YOUR_NAS_IP:3000/posts \
  -H "Content-Type: application/json" \
  -d '{"title": "New Post", "author": "Test User"}'
```

#### Check HTTP Status
```bash
curl -I http://YOUR_NAS_IP:3000/posts
# Should return: HTTP/1.1 200 OK
```

### 3. Test with Browser

Open these URLs in your web browser:

- Database overview: `http://YOUR_NAS_IP:3000`
- All posts: `http://YOUR_NAS_IP:3000/posts`
- Post #1: `http://YOUR_NAS_IP:3000/posts/1`
- All comments: `http://YOUR_NAS_IP:3000/comments`
- Profile: `http://YOUR_NAS_IP:3000/profile`

### 4. Test from Local Machine (if testing locally)

If testing on the build machine before deployment:

```bash
# Test localhost
curl http://localhost:3000/posts

# Or with pretty JSON
curl http://localhost:3000/posts | python3 -m json.tool
```

## Expected Responses

### Successful Response (200 OK)
```json
[
  {
    "id": 1,
    "title": "Post 1",
    "author": "John"
  },
  {
    "id": 2,
    "title": "Post 2",
    "author": "Doe"
  }
]
```

### Not Found (404)
```json
{}
```

### Server Error (500)
If the server is not running, you'll get a connection error.

## Troubleshooting

### Server Not Responding

1. **Check if service is running:**
   ```bash
   sudo synopkg status Json-Server
   ```

2. **Check logs:**
   ```bash
   tail -f /var/packages/Json-Server/var/service.log
   tail -f /var/packages/Json-Server/var/json-server.log
   ```

3. **Check port configuration:**
   ```bash
   cat /var/packages/Json-Server/var/config.ini
   ```

4. **Restart the service:**
   ```bash
   sudo synopkg stop Json-Server
   sudo synopkg start Json-Server
   ```

### Port Already in Use

If port 3000 is already in use, edit the config:
```bash
sudo nano /var/packages/Json-Server/var/config.ini
```

Change the port, then restart the service.

### Firewall Issues

Ensure port 3000 (or your configured port) is open in:
- Synology Firewall settings
- Your router/network firewall
