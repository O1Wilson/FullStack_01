// Set the default model tab as active and hide container
document.addEventListener("DOMContentLoaded", function() {
    document.querySelector('.tablinks').click();
    document.querySelector('.container').style.display = 'none';
});

// Function to toggle parameter dropdown visibility
function toggleParameters() {
    const parameterTable = document.querySelector('.tab');
    const button = document.getElementById('toggleParametersButton');

    // Toggle the visibility of the parameter table and container
    parameterTable.style.display = parameterTable.style.display === 'none' ? 'block' : 'none';
    button.textContent = parameterTable.style.display === 'none' ? 'Show Parameters' : 'Hide Parameters';
    document.querySelector('.container').style.display = parameterTable.style.display;
}

// JavaScript for switching between tabs
function openModel(evt, modelName) {
    var i, tabcontent, tablinks;

    // Hide all tab contents
    tabcontent = document.getElementsByClassName("tabcontent");
    for (i = 0; i < tabcontent.length; i++) {
        tabcontent[i].style.display = "none";
    }

    // Remove 'active' class from all tab links
    tablinks = document.getElementsByClassName("tablinks");
    for (i = 0; i < tablinks.length; i++) {
        tablinks[i].className = tablinks[i].className.replace(" active", "");
    }

    // Show the clicked tab content and mark the button as active
    document.getElementById(modelName).style.display = "block";
    evt.currentTarget.className += " active";
}

// Function to submit form data
async function submitForm(model) {
    try {

        // Show the loading popup
        document.getElementById('loadingPopup').style.display = 'flex';

        // Get the form data based on the active tab
        const formData = new FormData(document.getElementById(`${model}Form`));

        // Function to fill null values with defaults
        function fillNullWithDefault(fieldName, defaultValue) {
            if (!formData.has(fieldName) || formData.get(fieldName) === '') {
                formData.set(fieldName, defaultValue);
            }
            // Lowercase style and quality fields
            if (fieldName === 'style' || fieldName === 'quality') {
                formData.set(fieldName, formData.get(fieldName).toLowerCase());
            }
        }

        // Fill null values with defaults
        fillNullWithDefault('n', '1');
        fillNullWithDefault('quality', 'standard');
        fillNullWithDefault('style', 'natural');


        const data = {
            prompt: document.getElementById('prompt').value,
            n: parseInt(formData.get('n')),
            width: 1024,
            height: 1024,
            quality: formData.get('quality'),
            style: formData.get('style'),
            user: formData.get('user')
        };

        const response = await fetch(`http://ai-image-creation-dev.bioworldmerch.com:8001/generate-art/${model}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data),
        });

        if (!response.ok) {
            throw new Error('Failed to fetch images');
        }

        const result = await response.json(); // Assuming API returns JSON data

        // Extract the necessary data from the response
        const uploadData = responseData.data;

        const artContainer = document.getElementById('artContainer');
        artContainer.innerHTML = ''; // Clear existing content

        result.images.forEach(imageUrl => {
            // Create a new art-box for each image
            const artBox = document.createElement('div');
            artBox.className = 'art-box';

            const imageElement = new Image(); // Create image element
            imageElement.onload = function() {
                const aspectRatio = this.width / this.height;
                const targetHeight = 250;

                let targetWidth = targetHeight * aspectRatio;
                if (targetWidth > 439) { // Limit width to 439px if it exceeds
                    targetWidth = 439;
                }

                // Set width and height dynamically based on aspect ratio and constraints
                this.style.width = `${targetWidth}px`;
                this.style.height = `${targetHeight}px`;

                // Append image element to artBox after adjusting dimensions
                artBox.appendChild(imageElement);

                // Continue with hover icons creation
                const hoverIcons = document.createElement('div');
                hoverIcons.className = 'art-box-hover-icons';

                const downloadLink = document.createElement('a');
                downloadLink.href = '#';
                downloadLink.className = 'download-icon';
                downloadLink.onclick = () => downloadImage(model, imageUrl);
                const downloadIcon = document.createElement('i');
                downloadIcon.className = 'fas fa-download';
                downloadLink.appendChild(downloadIcon);

                const uploadLink = document.createElement('a');
                uploadLink.href = '#';
                uploadLink.className = 'upload-icon';
                const uploadIcon = document.createElement('i');
                uploadIcon.className = 'fas fa-upload';
                uploadLink.appendChild(uploadIcon);

                const deleteLink = document.createElement('a');
                deleteLink.href = '#';
                deleteLink.className = 'delete-icon';
                deleteLink.onclick = () => deleteImage(deleteLink);
                const deleteIcon = document.createElement('i');
                deleteIcon.className = 'fas fa-trash-alt';
                deleteLink.appendChild(deleteIcon);

                hoverIcons.appendChild(downloadLink);
                hoverIcons.appendChild(uploadLink);
                hoverIcons.appendChild(deleteLink);

                artBox.appendChild(hoverIcons);

                artContainer.appendChild(artBox);
            };

            // Set image source after defining onload function
            imageElement.src = `backend/generated_images${imageUrl}`;
            imageElement.alt = 'Generated Art';

        });

        const submissionMessage = document.getElementById('submissionMessage');
        submissionMessage.style.display = 'block';
        setTimeout(() => {
            submissionMessage.style.display = 'none';
        }, 3000);

        // Upload data
        const uploadResponse = await fetch('http://ai-image-creation-dev.bioworldmerch.com:8001/upload-data', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(uploadData),
        });

        if (!uploadResponse.ok) {
            throw new Error('Failed to upload data');
        }

    console.log('Data uploaded successfully');

    } catch (error) {
        console.error('Error fetching and displaying images:', error);

        document.getElementById('errorPopup').style.display = 'flex';
    } finally {
        // Hide the loading popup
        document.getElementById('loadingPopup').style.display = 'none';
    }
}

// Function to handle image download
async function downloadImage(imageUrl) {
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

// Function to handle image deletion
function deleteImage(deleteButton) {
    if (confirm("Are you sure you want to delete this image?")) {
        // Find the parent art-box element and remove it from the DOM
        const artBox = deleteButton.closest('.art-box');
        if (artBox) {
            artBox.remove();
            // Additional logic to be added
        }
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const uploadButtons = document.querySelectorAll(".upload-button");

    uploadButtons.forEach(button => {
        button.addEventListener("click", async () => {
            const imageContainer = button.closest(".image-container");
            const hoverImage = imageContainer.querySelector(".hover-image");
            const generatedImageFilename = imageContainer.dataset.generatedFilename;

            if (hoverImage && generatedImageFilename) {
                const imageUrl = hoverImage.src;
                const uploadData = {
                    images: [
                        {
                            imageUrl: imageUrl,
                            generatedImageFilename: generatedImageFilename
                        }
                    ]
                };

                try {
                    const response = await fetch('/upload', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(uploadData)
                    });
                    if (response.ok) {
                        alert('Image uploaded successfully!');
                    } else {
                        alert('Failed to upload image.');
                    }
                } catch (error) {
                    console.error('Error uploading image:', error);
                    alert('Failed to upload image. Check console for details.');
                }
            } else {
                alert('Image or generated filename is missing.');
            }
        });
    });
});