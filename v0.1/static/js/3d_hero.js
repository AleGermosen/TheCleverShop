// 3D Hero Animation with Three.js
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { STLLoader } from 'three/addons/loaders/STLLoader.js';

// Debug flag - set to true for detailed console logs
const DEBUG = true;

// Debug logger function
function debug(...args) {
    if (DEBUG) {
        console.log('[3D Hero]', ...args);
    }
}

document.addEventListener('DOMContentLoaded', function() {
    // Scene setup
    const container = document.getElementById('hero-canvas-container');
    if (!container) {
        console.error('Hero container not found!');
        return;
    }
    
    debug('Initializing 3D Hero section...');
    debug('Container dimensions:', container.clientWidth, 'x', container.clientHeight);
    
    // Create scene, camera, and renderer
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x000000); // Pure black background
    
    const camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 1000);
    // Position camera higher and further back for a better view
    camera.position.set(5, 5, 12);
    camera.lookAt(0, 0, 0);
    
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(container.clientWidth, container.clientHeight);
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap; // Softer shadows
    renderer.localClippingEnabled = true; // Enable clipping planes
    container.appendChild(renderer.domElement);
    
    debug('Renderer created and added to container');
    
    // OrbitControls for user interaction
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.enableZoom = false;
    controls.autoRotate = true;
    controls.autoRotateSpeed = 0.7; // Slower rotation speed
    // Adjust control boundaries to keep models in view
    controls.maxPolarAngle = Math.PI / 1.8; // Don't go below the horizon
    controls.minPolarAngle = Math.PI / 8;  // Don't go too high
    
    // Store controls reference in scene for access by other functions
    scene.userData.controls = controls;
    
    // Add debug visuals to help understand issues
    if (DEBUG) {
        debug('Debug mode active, but visual helpers disabled for clean look');
    }
    
    // Lighting
    const ambientLight = new THREE.AmbientLight(0x404040, 2.5); // Increased ambient light
    scene.add(ambientLight);
    
    const keyLight = new THREE.DirectionalLight(0xffffff, 1.2);
    keyLight.position.set(5, 5, 5);
    keyLight.castShadow = true;
    scene.add(keyLight);
    
    const mainFillLight = new THREE.DirectionalLight(0x2196f3, 0.8);
    mainFillLight.position.set(-5, 0, 5);
    scene.add(mainFillLight);
    
    const backLight = new THREE.DirectionalLight(0x4caf50, 0.8);
    backLight.position.set(0, -5, -5);
    scene.add(backLight);
    
    // Add a special spotlight just for this model
    const spotlight = new THREE.SpotLight(0xffffcc, 3);
    spotlight.position.set(0, 8, 5); // Position spotlight to match new camera angle
    spotlight.angle = Math.PI / 5; // Wider spotlight angle
    spotlight.penumbra = 0.5;
    spotlight.distance = 25;
    spotlight.castShadow = true;
    spotlight.shadow.bias = -0.0001;
    scene.add(spotlight);
    
    // Create a target object for the spotlight and position it at the model
    const spotlightTarget = new THREE.Object3D();
    spotlightTarget.position.set(0, 0, 0); // Default to origin since model isn't loaded yet
    scene.add(spotlightTarget);
    spotlight.target = spotlightTarget;
    
    // Add a secondary fill light from the side
    const fillLight = new THREE.SpotLight(0xffffcc, 1.5);
    fillLight.position.set(5, 5, -3);
    fillLight.angle = Math.PI / 6;
    fillLight.penumbra = 0.7;
    fillLight.distance = 20;
    fillLight.castShadow = false;
    scene.add(fillLight);
    
    // Model variables
    let currentModel;
    let maxHeight = 3;
    let currentHeight = 0;
    let isGrowing = true;
    let printingInProgress = true;
    let currentModelIndex = 0;
    let failedModels = [];
    
    // Define available models - ensure paths are correct
    const modelList = [
        { 
            type: 'stl',
            url: '/static/models/sample_print.stl',
            color: 0x4CAF50,
            displayName: 'Sample Print',
            fallbackUrl: '/static/models/fallback/cube.stl'
        },
        { 
            type: 'stl',
            url: '/static/models/pyramid.stl',
            color: 0xFF5722,
            displayName: 'Pyramid',
            fallbackUrl: '/static/models/fallback/cube.stl'
        },
        {
            type: 'geometry',
            name: 'torusKnot',
            color: 0x9C27B0,
            displayName: 'Torus Knot'
        },
        {
            type: 'stl',
            url: '/static/models/harry_potter_right.stl',
            fallbackUrl: '/static/models/fallback/cube.stl',
            color: 0xFFD700, // Gold color for Harry Potter
            displayName: 'Harry Potter Figure',
            // Special material settings for Harry Potter model
            materialSettings: {
                metalness: 0.8,
                roughness: 0.2,
                emissive: 0x222200,
                emissiveIntensity: 0.3,
                opacity: 1.0, // Fully opaque
                transparent: false // Not transparent
            }
        }
    ];
    
    // Function to check if STL model URLs are valid
    function validateModelUrls() {
        debug('Validating model list with', modelList.length, 'entries');
        
        const validatedModels = modelList.filter(model => {
            // Check if model is properly defined
            if (!model || typeof model !== 'object') {
                debug('Invalid model entry (not an object):', model);
                return false;
            }
            
            // Check model type
            if (!model.type || (model.type !== 'stl' && model.type !== 'geometry')) {
                debug('Invalid model type:', model.type);
                return false;
            }
            
            // For STL models, check URL
            if (model.type === 'stl' && (!model.url || typeof model.url !== 'string')) {
                debug('Invalid STL URL:', model.url);
                return false;
            }
            
            // For geometry models, check name
            if (model.type === 'geometry' && (!model.name || typeof model.name !== 'string')) {
                debug('Invalid geometry name:', model.name);
                return false;
            }
            
            return true;
        });
        
        // Log available models for debugging
        debug('Validated model list:', validatedModels.map(m => {
            if (m.type === 'stl') {
                return `STL: ${m.url} (${m.displayName || 'Unnamed'})`;
            } else {
                return `Geometry: ${m.name} (${m.displayName || 'Unnamed'})`;
            }
        }));
        
        return validatedModels;
    }
    
    // Get validated model list
    const validatedModels = validateModelUrls();
    
    // Model creation functions
    function createDefaultModel() {
        console.log('Creating default model (fallback)');
        // Remove existing model if any
        if (currentModel) scene.remove(currentModel);
        
        // Create geometric model
        const modelGeometry = new THREE.TorusKnotGeometry(1.5, 0.5, 64, 16);
        const modelMaterial = new THREE.MeshStandardMaterial({ 
            color: 0x4CAF50,
            roughness: 0.7,
            metalness: 0.2,
            transparent: true,
            opacity: 0.8,
            side: THREE.DoubleSide
        });
        currentModel = new THREE.Mesh(modelGeometry, modelMaterial);
        currentModel.position.y = 0;
        currentModel.castShadow = true;
        scene.add(currentModel);
        
        // Set initial clipping and height
        currentHeight = 0;
        updatePrintingEffect();
    }
    
    function createGeometryModel(modelType, color) {
        console.log(`Creating geometry model: ${modelType}`);
        // Remove existing model if any
        if (currentModel) scene.remove(currentModel);
        
        let geometry;
        
        switch(modelType) {
            case 'sphere':
                geometry = new THREE.SphereGeometry(1.5, 32, 32);
                break;
            case 'torusKnot':
                geometry = new THREE.TorusKnotGeometry(1.2, 0.4, 64, 16);
                break;
            case 'cube':
                geometry = new THREE.BoxGeometry(2, 2, 2);
                break;
            case 'torus':
                geometry = new THREE.TorusGeometry(1.2, 0.5, 16, 32);
                break;
            default:
                geometry = new THREE.TorusKnotGeometry(1.5, 0.5, 64, 16);
        }
        
        const modelMaterial = new THREE.MeshStandardMaterial({ 
            color: color || 0x4CAF50,
            roughness: 0.7,
            metalness: 0.2,
            transparent: true,
            opacity: 0.8,
            side: THREE.DoubleSide, // Render both sides of faces
            clippingPlanes: [] // Initialize with empty clipping planes
        });
        
        currentModel = new THREE.Mesh(geometry, modelMaterial);
        currentModel.position.y = 0;
        currentModel.castShadow = true;
        scene.add(currentModel);
        
        // Reset height and clipping for animation
        currentHeight = -2.5;
        maxHeight = 2.5;
        updatePrintingEffect();
        
        return Promise.resolve(); // Return resolved promise for consistent API
    }
    
    // Try to load an STL model, with fallback to default model
    function loadSTLModel(url, color, materialSettings) {
        debug('Attempting to load STL from:', url);
        
        // Check if URL is valid
        if (!url) {
            console.error('Invalid URL provided to loadSTLModel:', url);
            return Promise.reject(new Error('Invalid or undefined URL'));
        }
        
        // Apply /static/ prefix if URL doesn't already start with it
        if (!url.startsWith('/static/') && !url.startsWith('http')) {
            url = '/static/' + url.replace(/^\//, '');
            debug('Updated URL:', url);
        }
        
        // Check if we've already failed to load this model before
        if (failedModels.includes(url)) {
            debug(`Skipping previously failed model: ${url}`);
            // Try a fallback model if specified
            const currentModel = validatedModels.find(m => m.url === url);
            if (currentModel && currentModel.fallbackUrl) {
                debug(`Attempting to load fallback model: ${currentModel.fallbackUrl}`);
                return loadSTLModel(currentModel.fallbackUrl, color, materialSettings);
            }
            return Promise.reject(new Error('Previously failed to load'));
        }
        
        const loader = new STLLoader();
        debug('STLLoader created');
        
        return new Promise((resolve, reject) => {
            try {
                debug('Starting load request for', url);
                loader.load(
                    url,
                    function (geometry) {
                        debug('STL loaded successfully:', url);
                        
                        // Remove existing model if any
                        if (currentModel) scene.remove(currentModel);
                        
                        // Create a base material with defaults
                        const materialOptions = {
                            color: color || 0x4CAF50,
                            roughness: 0.5,
                            metalness: 0.3,
                            transparent: true,
                            opacity: 0.9,
                            side: THREE.DoubleSide,
                            flatShading: true,
                            clippingPlanes: [] // Initialize with empty clipping planes
                        };
                        
                        // Apply any custom material settings provided
                        if (materialSettings) {
                            Object.assign(materialOptions, materialSettings);
                            debug('Applied custom material settings:', materialSettings);
                        }
                        
                        // Special case for Harry Potter model - make it very visible
                        if (url.includes('harry_potter')) {
                            materialOptions.metalness = 0.8;
                            materialOptions.roughness = 0.2;
                            materialOptions.emissive = new THREE.Color(0x222200);
                            materialOptions.emissiveIntensity = 0.3;
                            materialOptions.transparent = false;
                            materialOptions.opacity = 1.0;
                            debug('Applied Harry Potter-specific material settings');
                        }
                        
                        // Create the final material
                        const material = new THREE.MeshStandardMaterial(materialOptions);
                        
                        // Add emissive if not already set but provided separately
                        if (!materialOptions.emissive && materialSettings?.emissive) {
                            material.emissive = new THREE.Color(materialSettings.emissive);
                            material.emissiveIntensity = materialSettings.emissiveIntensity || 0.5;
                        }
                        
                        try {
                            currentModel = new THREE.Mesh(geometry, material);
                            debug('Mesh created with geometry');
                            
                            // Using the editor-style approach for centering
                            geometry.computeBoundingSphere();
                            const center = geometry.boundingSphere.center;
                            
                            // Only apply standard centering for non-Harry Potter models
                            // Harry Potter models will be explicitly positioned in customizeHarryPotterModel
                            if (!url.includes('harry_potter')) {
                                currentModel.position.set(-center.x, -center.y, -center.z);
                                debug('Mesh centered at', -center.x, -center.y, -center.z);
                            } else {
                                debug('Skipping standard centering for Harry Potter model');
                            }
                            
                            // Handle scale using a more robust approach
                            geometry.computeBoundingBox();
                            const box = geometry.boundingBox;
                            const size = new THREE.Vector3();
                            box.getSize(size);
                            
                            // Make the Harry Potter model much larger than other models
                            let scaleFactor = 5 / Math.max(size.x, size.y, size.z); 
                            
                            // Special case for Harry Potter models - they need to be larger
                            if (url.includes('harry_potter')) {
                                scaleFactor = 15 / Math.max(size.x, size.y, size.z); // Reduced from 30 to 15
                                debug('Using larger scale for Harry Potter model:', scaleFactor);
                            }
                            
                            debug('Model dimensions:', size, 'Scale factor:', scaleFactor);
                            
                            // Scale the model appropriately
                            currentModel.scale.set(scaleFactor, scaleFactor, scaleFactor);
                            
                            // Apply specialized settings for specific models
                            if (url.includes('harry_potter')) {
                                customizeHarryPotterModel(currentModel, scene);
                            } else {
                                // Default position adjustment
                                currentModel.position.y = 0.5;
                            }
                            
                            currentModel.castShadow = true;
                            scene.add(currentModel);
                            debug('Model added to scene');
                            
                            // Reset height and clipping for animation
                            currentHeight = -1.5;
                            maxHeight = 1.5;
                            updatePrintingEffect();
                            
                            // Log success details
                            debug('Model details:', {
                                vertices: geometry.attributes.position.count,
                                boundingSphere: geometry.boundingSphere,
                                size: size,
                                scaleFactor: scaleFactor
                            });
                            
                            resolve();
                        } catch (err) {
                            console.error('Error processing STL geometry:', err);
                            failedModels.push(url);
                            
                            // Try a fallback model if specified
                            const currentModelDef = validatedModels.find(m => m.url === url);
                            if (currentModelDef && currentModelDef.fallbackUrl) {
                                debug(`Attempting to load fallback model: ${currentModelDef.fallbackUrl}`);
                                loadSTLModel(currentModelDef.fallbackUrl, color, materialSettings)
                                    .then(resolve)
                                    .catch(reject);
                            } else {
                                reject(err);
                            }
                        }
                    },
                    // Progress callback
                    function (xhr) {
                        if (xhr.lengthComputable) {
                            const percentComplete = (xhr.loaded / xhr.total) * 100;
                            debug(`${url} loading: ${Math.round(percentComplete)}%`);
                        }
                    },
                    // Error callback
                    function (error) {
                        console.error('STL loader error:', error, url);
                        failedModels.push(url);
                        
                        // Try a fallback model if specified
                        const currentModelDef = validatedModels.find(m => m.url === url);
                        if (currentModelDef && currentModelDef.fallbackUrl) {
                            debug(`Attempting to load fallback model: ${currentModelDef.fallbackUrl}`);
                            loadSTLModel(currentModelDef.fallbackUrl, color, materialSettings)
                                .then(resolve)
                                .catch(reject);
                        } else {
                            reject(error);
                        }
                    }
                );
            } catch (error) {
                console.error('Exception in STL loading:', error, url);
                failedModels.push(url);
                
                // Try a fallback model if specified
                const currentModelDef = validatedModels.find(m => m.url === url);
                if (currentModelDef && currentModelDef.fallbackUrl) {
                    debug(`Attempting to load fallback model: ${currentModelDef.fallbackUrl}`);
                    loadSTLModel(currentModelDef.fallbackUrl, color, materialSettings)
                        .then(resolve)
                        .catch(reject);
                } else {
                    reject(error);
                }
            }
        });
    }
    
    // Function to change the current model
    function changeModel() {
        // Check if there are valid models to display
        if (validatedModels.length === 0) {
            console.error('No valid models to display');
            return;
        }
        
        // Skip to the next model
        currentModelIndex = (currentModelIndex + 1) % validatedModels.length;
        const nextModel = validatedModels[currentModelIndex];
        
        // Verify the next model is valid
        if (!nextModel || !nextModel.type) {
            debug('Invalid model at index', currentModelIndex, nextModel);
            // Skip to the next model
            setTimeout(changeModel, 100);
            return;
        }
        
        // Set the model information
        setModelDisplay(nextModel);
        
        // Reset camera and controls to default positions before loading new model
        // This ensures consistent rotation around center
        camera.position.set(5, 5, 12);
        controls.target.set(0, 0, 0);
        controls.update();
        
        // Load the model
        if (nextModel.type === 'stl' && nextModel.url) {
            loadSTLModel(nextModel.url, nextModel.color, nextModel.materialSettings)
                .then(function() {
                    // Ensure controls are properly targeting the new model after loading
                    if (currentModel) {
                        // Default center if model doesn't have customized targeting
                        if (!controls.target || controls.target.equals(new THREE.Vector3(0, 0, 0))) {
                            controls.target.set(currentModel.position.x, currentModel.position.y, currentModel.position.z);
                            controls.update();
                            debug('Updated controls target to new model position');
                        }
                    }
                })
                .catch(function(error) {
                    console.error('Error loading model:', error);
                    // Skip to the next model when we fail
                    setTimeout(changeModel, 100);
                });
        } else if (nextModel.type === 'geometry' && nextModel.name) {
            createGeometryModel(nextModel.name, nextModel.color)
                .then(function() {
                    // Ensure controls are targeting geometric models too
                    if (currentModel) {
                        controls.target.set(currentModel.position.x, currentModel.position.y, currentModel.position.z);
                        controls.update();
                    }
                });
        } else {
            debug('Invalid model configuration:', nextModel);
            // Skip to the next model
            setTimeout(changeModel, 100);
        }
    }
    
    // Function to update the display with current model info
    function setModelDisplay(model) {
        if (!model) {
            debug('Invalid model passed to setModelDisplay');
            return;
        }
        
        // Get a display name, with fallback
        const displayName = model.displayName || 
                          (model.type === 'stl' ? 'STL Model' : 'Geometric Model');
        
        // Update the badge text to show what's being printed
        const layerText = document.querySelector('.layer-badge span:not(.layer-indicator)');
        if (layerText) {
            layerText.textContent = `Printing: ${displayName}`;
        }
        debug(`Now displaying: ${displayName}`);
    }
    
    // Helper function to get a display name for the model
    function getModelDisplayName(model) {
        if (model.displayName) return model.displayName;
        
        if (model.type === 'stl') {
            // Extract filename from path without extension
            const filename = model.url.split('/').pop().split('.')[0];
            // Convert snake_case or kebab-case to Title Case
            return filename
                .replace(/[-_]/g, ' ')
                .replace(/\w\S*/g, w => w.replace(/^\w/, c => c.toUpperCase()));
        } else {
            // Convert camelCase to Title Case
            return model.name
                .replace(/([A-Z])/g, ' $1')
                .replace(/^./, str => str.toUpperCase());
        }
    }
    
    // Create a function to handle the "printing" effect via clipping planes
    function updatePrintingEffect() {
        if (!currentModel) return;
        
        // Apply clipping plane for the printing effect
        const clipPlane = new THREE.Plane(new THREE.Vector3(0, -1, 0), currentHeight);
        
        if (currentModel.material) {
            currentModel.material.clippingPlanes = [clipPlane];
            
            // Ensure the material is fully opaque and not wireframe
            currentModel.material.wireframe = false;
            currentModel.material.transparent = false;
            currentModel.material.opacity = 1.0;
            currentModel.material.needsUpdate = true;
        }
    }
    
    // Initialize the first model - try STL first, fall back to geometry
    console.log('Initializing first model');
    const firstModel = validatedModels[0];
    setModelDisplay(firstModel);
    
    if (firstModel.type === 'stl') {
        loadSTLModel(firstModel.url, firstModel.color, firstModel.materialSettings).catch(e => {
            console.error("Error loading initial STL, using default model", e);
            createGeometryModel('torusKnot', firstModel.color);
        });
    } else {
        createGeometryModel(firstModel.name, firstModel.color);
    }
    
    // Add a change model button
    const nextModelButton = document.createElement('button');
    nextModelButton.textContent = 'Next Model';
    nextModelButton.style.position = 'absolute';
    nextModelButton.style.bottom = '10px';
    nextModelButton.style.right = '10px';
    nextModelButton.style.zIndex = '100';
    nextModelButton.style.padding = '5px 10px';
    nextModelButton.style.background = '#333';
    nextModelButton.style.color = 'white';
    nextModelButton.style.border = 'none';
    nextModelButton.style.borderRadius = '4px';
    nextModelButton.style.cursor = 'pointer';
    nextModelButton.onclick = changeModel;
    container.appendChild(nextModelButton);
    
    // Set up model transition state
    let modelCompleted = false;
    let transitionScheduled = false;
    
    // Animation loop
    function animate() {
        requestAnimationFrame(animate);
        
        // Slow auto-rotation
        controls.update();
        
        // Enable printing effect animation
        if (printingInProgress && currentModel) {
            if (isGrowing) {
                currentHeight += 0.01;
                if (currentHeight >= maxHeight) {
                    isGrowing = false;
                    // Pause at the top before switching to the next model
                    setTimeout(() => {
                        // Change to the next model after the current one completes
                        changeModel();
                        
                        // Reset animation state for the new model
                        isGrowing = true;
                        currentHeight = -1.5;
                    }, 2000);
                }
            }
            updatePrintingEffect();
        }
        
        // Constantly ensure the camera is looking at the model
        if (currentModel) {
            // Get the center of the current model
            const box = new THREE.Box3().setFromObject(currentModel);
            const center = box.getCenter(new THREE.Vector3());
            // Update controls target to match model center
            controls.target.copy(center);
        }
        
        renderer.render(scene, camera);
    }
    
    // Start animation
    animate();
    
    // Handle resize
    window.addEventListener('resize', function() {
        camera.aspect = container.clientWidth / container.clientHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(container.clientWidth, container.clientHeight);
    });
    
    console.log('3D Hero section initialized successfully');
});

// Function to customize Harry Potter models specifically
function customizeHarryPotterModel(model, scene) {
    debug('Applying Harry Potter model customizations');
    
    // Get the original center
    const geometry = model.geometry;
    geometry.computeBoundingSphere();
    const center = geometry.boundingSphere.center;
    const scale = model.scale.x; // Get current scale
    
    // Position model to align with the axes at the true center of the geometry
    model.position.set(-center.x * scale, -center.y * scale, -center.z * scale);
    
    // Keep model upright without any tilt
    model.rotation.set(0, 0, 0);
    
    // Make camera look at the model's computed center
    const modelCenter = new THREE.Vector3(-center.x * scale, -center.y * scale, -center.z * scale);
    const cameraControls = scene.userData.controls;
    if (cameraControls) {
        cameraControls.target.copy(modelCenter);
        debug('Camera target set to model center');
    }
    
    // Update the existing spotlights to target the model center
    scene.traverse(function(object) {
        if (object instanceof THREE.SpotLight) {
            if (!object.target || object.target === model) {
                // Create a target object for the spotlight and position it at the model
                const spotlightTarget = new THREE.Object3D();
                spotlightTarget.position.copy(modelCenter);
                scene.add(spotlightTarget);
                object.target = spotlightTarget;
                debug('Updated spotlight target to model center');
            }
        }
    });
    
    debug('Model centered and positioned for optimal viewing');
    return model;
} 