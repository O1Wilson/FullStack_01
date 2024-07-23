# FullStack_01
Full stack web interface developed by Owen Wilson. Designed for creative teams.

![Screenshot 2024-07-23 124022](https://github.com/user-attachments/assets/4b7aa75a-33a6-45ec-ac5b-23a899dbcaf4)
(^Slideshow Background^)

### User Story 1: Default Tab Activation and Container Visibility

**As a** user  
**I want to** see the default model tab activated when I first load the page  
**So that** I don't have to manually select a tab and adjust visibility

**Acceptance Criteria:**
- Upon loading the page, the script automatically clicks the first tab link with the class `tablinks`.
- The container with the class `container` is hidden on page load.
  
![Screenshot 2024-07-23 124544](https://github.com/user-attachments/assets/63de63e9-341a-439a-b64c-cbd075df373a)

---

### User Story 2: Toggle Parameter Dropdown

**As a** user  
**I want to** show or hide the parameter table when I click a button  
**So that** I can view or hide additional settings as needed

**Acceptance Criteria:**
- When the button with the ID `toggleParametersButton` is clicked, the visibility of the parameter table with the class `tab` toggles between visible and hidden.
- The button text changes to "Show Parameters" or "Hide Parameters" based on the visibility state.

![Screenshot 2024-07-23 124649](https://github.com/user-attachments/assets/8a01747b-520f-4be9-b7f7-4143d54235a0)

---

### User Story 3: Tab Navigation

**As a** user  
**I want to** switch between different model tabs  
**So that** I can view different content associated with each model

**Acceptance Criteria:**
- Clicking on a tab link with the class `tablinks` hides all other tab contents and removes the 'active' class from other tab links.
- The content associated with the clicked tab (identified by `modelName`) is displayed.
- The clicked tab link receives the 'active' class.

![Screenshot 2024-07-23 124727](https://github.com/user-attachments/assets/65ad2b2e-ff0c-4b39-9d0c-739c56533fe2)

---

### User Story 4: Form Submission and Default Values

**As a** user  
**I want to** submit form data and have missing values filled with defaults  
**So that** I can ensure all necessary data is included in the request

**Acceptance Criteria:**
- When the form is submitted, missing or empty fields are populated with default values (`n` is `1`, `quality` is `standard`, `style` is `natural`).
- The form data is sent to the server as a JSON object with properties including `prompt`, `n`, `width`, `height`, `quality`, `style`, and `user`.
  
![Screenshot 2024-07-23 124809](https://github.com/user-attachments/assets/21ae2a10-ca36-4daf-9ccb-500fa478d3c5)
![Screenshot 2024-07-23 124828](https://github.com/user-attachments/assets/ae9b1f78-d22e-4765-b6f9-30f1ca178159)

---

### User Story 5: Display Generated Images

**As a** user  
**I want to** see the generated images displayed in a container  
**So that** I can view and interact with the results of the image generation

**Acceptance Criteria:**
- After fetching images from the server, each image is displayed in a container with the ID `artContainer`.
- Images are resized to fit within a height of 250px while maintaining aspect ratio and a maximum width of 439px.
- Each image has hover icons for downloading, uploading, and deleting.

![Screenshot 2024-07-23 124932](https://github.com/user-attachments/assets/3ac5f963-b5ad-403f-816b-560fb9bca853)
![Screenshot 2024-07-23 124949](https://github.com/user-attachments/assets/35a33d31-f59a-48e7-a9f5-79f02fde32a1)

---

### User Story 6: Image Download

**As a** user  
**I want to** download an image by clicking a download icon  
**So that** I can save the image to my local device

**Acceptance Criteria:**
- Clicking the download icon triggers a download of the image.
- The image is fetched as a Blob, and a temporary anchor element is created to facilitate the download.
- The filename for the download is derived from the server response.
  
![Screenshot 2024-07-23 125008](https://github.com/user-attachments/assets/4c2d184d-6c65-42f4-99aa-08cab6a6d977)

---

### User Story 7: Image Deletion

**As a** user  
**I want to** delete an image by clicking a delete icon  
**So that** I can remove unwanted images from the view

**Acceptance Criteria:**
- Clicking the delete icon prompts a confirmation dialog.
- If confirmed, the image is removed from the DOM.
- Additional server-side logic for image deletion can be included if necessary.

![Screenshot 2024-07-23 125019](https://github.com/user-attachments/assets/47771739-4c59-42a9-b874-b33a2c349b1f)

---

### User Story 8: Image Upload

**As a** user  
**I want to** upload an image by clicking an upload button  
**So that** I can submit the image to the server for further processing

**Acceptance Criteria:**
- Clicking the upload button triggers a POST request to the `/upload` endpoint with image data.
- If the upload is successful, an alert confirms the success.
- If the upload fails, an alert notifies the user of the failure.

![Screenshot 2024-07-23 125101](https://github.com/user-attachments/assets/ef2c41a5-9f4f-43d2-ac0a-35e594674c18)

---

# User Story 9: AI Image Metadata Management

## Overview

This system captures, stores, retrieves, and manages metadata for AI-generated images. It ensures that all relevant details about each image are maintained and can be efficiently managed.

## Features

### Metadata Capture

- **Filename**: The name of the generated image file.
- **Created Datetime**: The timestamp when the image was generated.
- **Model**: The AI model used for image generation (e.g., DALL-E, Stable Diffusion).
- **Prompt**: The text prompt used to generate the image.
- **Width**: The width of the generated image.
- **Height**: The height of the generated image.
- **Quality**: The quality setting used (if applicable).
- **Style**: The style setting used (if applicable).
- **User**: The identifier of the user who requested the image.
- **Filepath**: The location where the image file is stored.

### Metadata Storage

- Metadata is stored in a database table named `ImageMetadata`.
- The table captures all the above fields and associates them with the generated image file.
![Screenshot 2024-07-23 120302](https://github.com/user-attachments/assets/89178419-b483-4295-b696-1263abde6722)

### Metadata Retrieval

- Metadata for any generated image can be retrieved by querying the `/api/metadata` endpoint with the image's filename.
- The response includes all the captured metadata fields.
![Screenshot 2024-07-23 120500](https://github.com/user-attachments/assets/ec00cee1-398a-4458-aeed-0e1e3c629eb8)

### Metadata Management

- The system performs regular cleanups to manage storage efficiently.
- Images and their metadata older than 48 hours are automatically deleted.
![Screenshot 2024-07-23 120912](https://github.com/user-attachments/assets/40334d14-36b5-4dd6-ac39-c51bac058724)

### Error Handling

- Errors during image generation or metadata capture are handled gracefully.
- Appropriate error messages are provided when issues arise.

## Example Workflow

1. Submit a request to generate an image using the `/generate-art/dalle` endpoint with a prompt and other parameters.
2. The system generates the image and saves it to the `generated_images` directory.
3. The system creates a metadata entry in the `ImageMetadata` database table with all the relevant details.
4. Retrieve the metadata for the image using the `/api/metadata` endpoint by providing the filename.
5. Images older than 48 hours are automatically deleted along with their metadata.

# User Story 10: Query Table with Enhanced Functionality

## Overview

This feature introduces an interactive query table designed to facilitate the management and viewing of metadata for AI-generated images. The table supports dynamic sorting, filtering, and detailed metadata viewing to enhance user interaction and data management.
![Screenshot 2024-07-23 114630](https://github.com/user-attachments/assets/b5b98361-23d4-41f8-95b4-15b86e119125)
(^Sample Data^)

## Features

### Table Interactivity

- **Sorting**: Clickable table headers enable sorting by columns. Indicators are displayed for ascending and descending order.
- **Filtering**: Clickable headers provide access to filter options. Filters persist until toggled off and automatically close when clicking outside the filter area.
- **Search**: Real-time search functionality allows users to quickly locate entries based on text input.

### Metadata Viewing

- **Prompt Pop-up**: Each row includes a "Prompt" button that triggers a pop-up displaying the associated prompt text.
- **Image Enlargement**: Clicking on an image thumbnail opens a separate pop-up window showing an enlarged view of the image.

### User Experience Enhancements

- **Automatic Filter Closure**: Filters automatically close when clicking elsewhere on the page, ensuring a clutter-free interface.
- **Responsive Design**: Pop-ups and interactive elements are designed to fit seamlessly within the existing webpage theme.

## Example Workflow

1. **Sort Data**: Click on a table header to sort the data by that column. The sorting direction toggles between ascending and descending.
2. **Filter Data**: Click on a filterable header to access filter options. Check or uncheck filter values to refine the displayed data.
3. **Search Data**: Enter a search query in the search input to filter table entries in real-time.
4. **View Metadata**: Click the "Prompt" button in a row to view the full prompt text in a pop-up. Click on an image thumbnail to enlarge the image in a separate pop-up window.
5. **Close Pop-ups**: Click outside the filter area or use the close buttons on pop-ups to hide them.

These enhancements provide a more interactive and user-friendly experience for managing and viewing metadata in the query table.
