import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { STLLoader } from 'three/addons/loaders/STLLoader.js';
import TWEEN from 'tweenjs';

export default class ThreeDHero {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.options = {
            autoRotate: true,
            autoRotateSpeed: 2.0,
            transitionDuration: 1000,
            backgroundColor: 0x222222,
            ambientLightIntensity: 0.6,
            directionalLightIntensity: 0.8,
            ...options
        };

        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(this.options.backgroundColor);
        
        this.camera = new THREE.PerspectiveCamera(
            45,
            this.container.clientWidth / this.container.clientHeight,
            0.1,
            1000
        );
        this.camera.position.set(8, 8, 8);
        
        this.renderer = new THREE.WebGLRenderer({ antialias: true });
        this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
        this.renderer.setPixelRatio(window.devicePixelRatio);
        this.renderer.shadowMap.enabled = true;
        this.container.appendChild(this.renderer.domElement);
        
        this.controls = new OrbitControls(this.camera, this.renderer.domElement);
        this.controls.enableDamping = true;
        this.dampingFactor = 0.05;
        this.controls.autoRotate = this.options.autoRotate;
        this.controls.autoRotateSpeed = this.options.autoRotateSpeed;
        this.controls.enableZoom = false;
        this.controls.target.set(0, 0, 0);
        this.controls.update();
        
        this.setupLights();
        this.currentModel = null;
        this.isTransitioning = false;
        
        this.animate();
        this.setupEventListeners();
    }

    setupLights() {
        const ambientLight = new THREE.AmbientLight(0xffffff, this.options.ambientLightIntensity);
        this.scene.add(ambientLight);
        
        const directionalLight = new THREE.DirectionalLight(0xffffff, this.options.directionalLightIntensity);
        directionalLight.position.set(1, 1, 1);
        this.scene.add(directionalLight);
        
        const backLight = new THREE.DirectionalLight(0xffffff, 0.4);
        backLight.position.set(-1, -1, -1);
        this.scene.add(backLight);
    }

    async changeModel(modelConfig) {
        if (this.isTransitioning) return;
        this.isTransitioning = true;

        // Create transition animation
        const transitionGroup = new THREE.Group();
        this.scene.add(transitionGroup);

        // Fade out current model if exists
        if (this.currentModel) {
            const fadeOutTween = new TWEEN.Tween(this.currentModel.material)
                .to({ opacity: 0 }, this.options.transitionDuration / 2)
                .easing(TWEEN.Easing.Quadratic.Out)
                .onComplete(() => {
                    this.scene.remove(this.currentModel);
                });
            fadeOutTween.start();
        }

        // Load new model
        const loader = new STLLoader();
        const geometry = await loader.loadAsync(modelConfig.url);
        
        const material = new THREE.MeshStandardMaterial({
            color: modelConfig.color,
            roughness: modelConfig.roughness || 0.5,
            metalness: modelConfig.metalness || 0.3,
            side: THREE.DoubleSide,
            transparent: true,
            opacity: 0
        });

        if (modelConfig.emissive) {
            material.emissive = new THREE.Color(modelConfig.emissive);
            material.emissiveIntensity = modelConfig.emissiveIntensity || 0.3;
        }

        const mesh = new THREE.Mesh(geometry, material);
        
        // Center and scale the model using Bounding Box
        geometry.computeBoundingBox();
        const box = geometry.boundingBox;
        const center = new THREE.Vector3();
        box.getCenter(center); // Calculate center of the bounding box
        mesh.position.set(-center.x, -center.y, -center.z); // Offset by the negative center
        
        const size = new THREE.Vector3();
        box.getSize(size);
        
        const scaleFactor = modelConfig.scaleFactor || (3 / Math.max(size.x, size.y, size.z));
        mesh.scale.set(scaleFactor, scaleFactor, scaleFactor);
        
        // Apply custom rotation if specified
        if (modelConfig.customRotation) {
            mesh.rotation.set(
                modelConfig.customRotation[0] || 0,
                modelConfig.customRotation[1] || 0,
                modelConfig.customRotation[2] || 0
            );
        }

        // Add to transition group
        transitionGroup.add(mesh);
        
        // Immediately set custom camera position if specified
        if (modelConfig.customCameraPosition) {
            this.camera.position.set(
                modelConfig.customCameraPosition[0],
                modelConfig.customCameraPosition[1],
                modelConfig.customCameraPosition[2]
            );
            this.controls.update(); // Update controls to reflect new position
        }
        
        // Animate entrance
        const entranceTween = new TWEEN.Tween(material)
            .to({ opacity: 1 }, this.options.transitionDuration / 2)
            .easing(TWEEN.Easing.Quadratic.In)
            .onComplete(() => {
                this.scene.remove(transitionGroup);
                this.scene.add(mesh);
                this.currentModel = mesh;
                this.isTransitioning = false;
            });
        
        entranceTween.start();
    }

    animate() {
        requestAnimationFrame(() => this.animate());
        TWEEN.update();
        this.controls.update();
        this.renderer.render(this.scene, this.camera);
    }

    setupEventListeners() {
        window.addEventListener('resize', () => {
            this.camera.aspect = this.container.clientWidth / this.container.clientHeight;
            this.camera.updateProjectionMatrix();
            this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
        });
    }

    toggleAutoRotate() {
        this.controls.autoRotate = !this.controls.autoRotate;
        return this.controls.autoRotate;
    }

    resetCamera() {
        this.camera.position.set(8, 8, 8);
        this.controls.target.set(0, 0, 0);
        this.controls.update();
    }
}

// Export the class for use in other files
// if (typeof module !== 'undefined' && module.exports) {
//     module.exports = ThreeDHero;
// }
