Write-Host "Starting script..."

$filePath = "dataset\train\images\E003.jpg"
$uri = "http://localhost:8000/detect"
$boundary = "----WebKitFormBoundary" + ([System.Guid]::NewGuid().ToString("N"))
$LF = "`r`n"

# Check if file exists
if (-not (Test-Path $filePath)) {
    Write-Error "File not found: $filePath"
    exit
}

# Read file
$fileBytes = [System.IO.File]::ReadAllBytes($filePath)
$fileName = [System.IO.Path]::GetFileName($filePath)

# Build multipart content manually
$preBody = (
    "--$boundary$LF" +
    "Content-Disposition: form-data; name=`"file`"; filename=`"$fileName`"$LF" +
    "Content-Type: image/jpeg$LF$LF"
) -replace "`n", "`r`n"

$postBody = "$LF--$boundary--$LF"

# Convert to bytes
$preBodyBytes = [System.Text.Encoding]::UTF8.GetBytes($preBody)
$postBodyBytes = [System.Text.Encoding]::UTF8.GetBytes($postBody)

# Combine all into one byte array
$fullRequest = New-Object System.IO.MemoryStream
$fullRequest.Write($preBodyBytes, 0, $preBodyBytes.Length)
$fullRequest.Write($fileBytes, 0, $fileBytes.Length)
$fullRequest.Write($postBodyBytes, 0, $postBodyBytes.Length)
$fullRequest.Position = 0

# Send the HTTP request
$webRequest = [System.Net.WebRequest]::Create($uri)
$webRequest.Method = "POST"
$webRequest.ContentType = "multipart/form-data; boundary=$boundary"
$webRequest.ContentLength = $fullRequest.Length

$reqStream = $webRequest.GetRequestStream()
$fullRequest.WriteTo($reqStream)
$reqStream.Close()

# Get the response
try {
    $response = $webRequest.GetResponse()
    $reader = New-Object System.IO.StreamReader($response.GetResponseStream())
    $responseBody = $reader.ReadToEnd()
    Write-Host "Response received:`n$responseBody"
}
catch {
    Write-Error "Request failed: $_"
}
