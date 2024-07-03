function fetchImages(page) {
    return new Promise((resolve, reject) => {
        // Adjust the API endpoint to fetch images from the uploaded_images folder
        fetch(`/api/uploaded_images?page=${page}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to fetch images');
                }
                return response.json();
            })
            .then(data => resolve(data.images))
            .catch(error => reject(error));
    });
}

let page = 1;
let isLoading = false; // Track if images are currently being loaded

function loadImages() {
    if (isLoading) return;
    isLoading = true;

    fetchImages(page).then(data => {
        const gallery = document.querySelector('.gallery');

        data.forEach(image => {
            const galleryItem = document.createElement('div');
            galleryItem.classList.add('gallery-item');

            // Create image element
            const img = document.createElement('img');
            img.src = `/uploaded_images/${image}`;
            img.alt = 'Uploaded Image';
            img.style.maxWidth = '250px';  // Set maximum width
            img.style.maxHeight = '250px'; // Set maximum height
            img.style.borderRadius = '8px'; // Apply border radius

            // Append image to gallery item
            galleryItem.appendChild(img);

            // Append gallery item to gallery
            gallery.appendChild(galleryItem);
        });

        // Increase page count after appending images
        page++;
        isLoading = false;
    }).catch(error => {
        console.error('Error loading images:', error);
        isLoading = false; // Reset isLoading flag on error
    });
}

// Load initial images
loadImages();

// Throttle scroll event
window.addEventListener('scroll', () => {
    if (window.innerHeight + window.scrollY >= document.body.offsetHeight - 100) {
        loadImages();
    }
});

// Inside the loop where you create gallery items
data.forEach(image => {
    const galleryItem = document.createElement('div');
    galleryItem.classList.add('gallery-item');
    galleryItem.innerHTML = `<img src="/uploaded_images/${image}" alt="Uploaded Image">`;

    // Create hover icons
    const hoverIcons = document.createElement('div');
    hoverIcons.className = 'art-box-hover-icons';

    // Download button
    const downloadLink = document.createElement('a');
    downloadLink.href = '#';
    downloadLink.className = 'download-icon';
    downloadLink.onclick = () => downloadImage(model, `/uploaded_images/${image}`); // Pass image URL here
    const downloadIcon = document.createElement('i');
    downloadIcon.className = 'fas fa-download';
    downloadLink.appendChild(downloadIcon);
    hoverIcons.appendChild(downloadLink);

    /// View button
    const viewLink = document.createElement('a');
    viewLink.href = '#';
    viewLink.className = 'view-icon';
    const viewIcon = document.createElement('i');
    viewIcon.className = 'fas fa-eye';
    viewLink.appendChild(viewIcon);
    viewLink.onclick = () => showFocusOverlay(`/uploaded_images/${image}`, 'Image Details'); // Call showFocusOverlay function
    hoverIcons.appendChild(viewLink);

    // Delete button
    const deleteLink = document.createElement('a');
    deleteLink.href = '#';
    deleteLink.className = 'delete-icon';
    deleteLink.onclick = () => deleteImage(deleteLink); // Call deleteImage function
    const deleteIcon = document.createElement('i');
    deleteIcon.className = 'fas fa-trash-alt';
    deleteLink.appendChild(deleteIcon);
    hoverIcons.appendChild(deleteLink);

    galleryItem.appendChild(hoverIcons);
    gallery.appendChild(galleryItem);
});

async function showFocusOverlay(imageUrl, filename) {
    // Update focused image
    const focusedImage = document.getElementById('focused-image');
    focusedImage.src = imageUrl;

    // Fetch metadata from your backend
    try {
        const response = await fetch(`/api/metadata?filename=${filename}`);
        if (!response.ok) {
            throw new Error('Failed to fetch metadata');
        }
        const metadata = await response.json();

        // Update image details
        const imageDetails = document.querySelector('.image-details');
        imageDetails.innerHTML = `
            <p><strong>Filename:</strong> ${metadata.filename}</p>
            <p><strong>Timestamp:</strong> ${metadata.timestamp}</p>
            <p><strong>Model:</strong> ${metadata.model}</p>
            <p><strong>Prompt:</strong> ${metadata.prompt}</p>
            <p><strong>Dimensions:</strong> ${metadata.width} x ${metadata.height}</p>
            <p><strong>Quality:</strong> ${metadata.quality}</p>
            <p><strong>Style:</strong> ${metadata.style}</p>
            <p><strong>User:</strong> ${metadata.user}</p>
        `;

        // Show focus overlay
        const focusOverlay = document.querySelector('.focus-overlay');
        focusOverlay.style.display = 'block';

        // Disable scrolling on the body while overlay is open
        document.body.style.overflow = 'hidden';
    } catch (error) {
        console.error('Error fetching metadata:', error);
        // Handle error display if needed
    }
}

// Function to handle image download
async function downloadImage(model, imageUrl) {
    try {
        // Fetch the image content as a Blob
        const response = await fetch(imageUrl);
        const blob = await response.blob(); // Convert response to Blob

        // Create a temporary anchor element
        const link = document.createElement('a');

        // Create a Blob URL to the image data
        const url = URL.createObjectURL(blob);
        link.href = url; // Set anchor's href to Blob URL

        // Set the download attribute to the filename
        const filename = response.headers.get('Content-Disposition')?.split('filename=')[1] || 'image.jpg';
        link.download = filename; // Set download filename

        // Append the anchor to the body and trigger the click event
        document.body.appendChild(link);
        link.click();

        // Clean up: remove the anchor element and revoke the Blob URL
        document.body.removeChild(link);
        URL.revokeObjectURL(url); // Revoke Blob URL to free up memory
    } catch (error) {
        console.error('Error downloading image:', error);
        alert('Failed to download image. Check console for details.');
    }
}

// Function to handle image deletion // NOTE TO SELF: REPLACE WITH LOGIC THAT DELETES IT FROM SERVER IF THE UPLOADER DELETES IT
function deleteImage(deleteButton) {
    if (confirm("Are you sure you want to delete this image?")) {
        // Find the parent art-box element and remove it from the DOM
        const artBox = deleteButton.closest('.art-box');
        if (artBox) {
            artBox.remove();
        }
    }
}