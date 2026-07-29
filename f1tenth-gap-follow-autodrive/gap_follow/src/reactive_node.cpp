#include "rclcpp/rclcpp.hpp"
#include "sensor_msgs/msg/laser_scan.hpp"
#include "std_msgs/msg/float32.hpp"
#include "visualization_msgs/msg/marker.hpp"

#include <vector>
#include <algorithm>
#include <cmath>

// Definimos M_PI por si el compilador no lo reconoce
#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

class ReactiveFollowGap : public rclcpp::Node {
public:
    ReactiveFollowGap() : Node("reactive_node") {
        // Publicadores principales
        throttle_pub = this->create_publisher<std_msgs::msg::Float32>(
            "/autodrive/f1tenth_1/throttle_command", 10);
        steering_pub = this->create_publisher<std_msgs::msg::Float32>(
            "/autodrive/f1tenth_1/steering_command", 10);

        // NUEVO: scan procesado para ver el obstáculo en RViz
        processed_scan_pub = this->create_publisher<sensor_msgs::msg::LaserScan>(
            "/processed_scan", 10);

        // NUEVO: visualización de la flecha de dirección
        marker_pub = this->create_publisher<visualization_msgs::msg::Marker>(
            "/visualization_marker", 10);

        // Suscriptor LiDAR
        scan_sub = this->create_subscription<sensor_msgs::msg::LaserScan>(
            "/autodrive/f1tenth_1/lidar", 10,
            std::bind(&ReactiveFollowGap::lidar_callback, this, std::placeholders::_1));
    }

private:
    void lidar_callback(const sensor_msgs::msg::LaserScan::ConstSharedPtr scan_msg) {
        auto ranges = scan_msg->ranges;
        int size = ranges.size();

        // 1. VISIÓN FRONTAL
        float view_angle = 70.0 * M_PI / 180.0;
        int min_idx = ((-view_angle) - scan_msg->angle_min) / scan_msg->angle_increment;
        int max_idx = ((view_angle) - scan_msg->angle_min) / scan_msg->angle_increment;

        min_idx = std::max(0, min_idx);
        max_idx = std::min(size - 1, max_idx);

        // 2. PREPROCESAMIENTO
        for (int i = 0; i < size; i++) {
            if (!std::isfinite(ranges[i]) || i < min_idx || i > max_idx) {
                ranges[i] = 0.0;
            }
            if (ranges[i] > 10.0) ranges[i] = 10.0;
        }

        // 3. OBSTÁCULO DINÁMICO (Inyectado a 0.5m para que sea MUY visible)
        // static float obstacle_pos = 0.0;
        // static bool direction = true;

        // obstacle_pos += (direction ? 0.008 : -0.008);
        // if (obstacle_pos > 0.35 || obstacle_pos < -0.35)
        //     direction = !direction;

        // int obs_idx = (obstacle_pos - scan_msg->angle_min) / scan_msg->angle_increment;

        // for (int i = -12; i <= 12; i++) {
        //     int idx = obs_idx + i;
        //     if (idx >= min_idx && idx <= max_idx) {
        //         ranges[idx] = 0.5; 
        //     }
        // }

        // 4. BURBUJA
        int closest_index = min_idx;
        float min_dist = 10.0;
        for (int i = min_idx; i <= max_idx; i++) {
            if (ranges[i] > 0.1 && ranges[i] < min_dist) {
                min_dist = ranges[i];
                closest_index = i;
            }
        }

        int bubble_radius = 18;
        for (int i = -bubble_radius; i <= bubble_radius; i++) {
            int idx = closest_index + i;
            if (idx >= 0 && idx < size)
                ranges[idx] = 0.0;
        }

        // 5. GAP MÁS GRANDE
        int max_start = min_idx, max_end = min_idx;
        int current_start = min_idx;
        bool in_gap = false;

        for (int i = min_idx; i <= max_idx; i++) {
            if (ranges[i] > 1.2) {
                if (!in_gap) {
                    current_start = i;
                    in_gap = true;
                }
            } else {
                if (in_gap) {
                    if ((i - current_start) > (max_end - max_start)) {
                        max_start = current_start;
                        max_end = i;
                    }
                    in_gap = false;
                }
            }
        }

        if (in_gap && (size - 1 - current_start) > (max_end - max_start)) {
            max_start = current_start;
            max_end = size - 1;
        }

        // 6. CONTROL
        int best_index = (max_start + max_end) / 2;
        float angle = scan_msg->angle_min + best_index * scan_msg->angle_increment;

        std_msgs::msg::Float32 throttle_msg;
        std_msgs::msg::Float32 steering_msg;
        steering_msg.data = angle;

        if (std::abs(angle) < 0.1) {
            throttle_msg.data = 0.25;
        } else {
            throttle_msg.data = 0.12;
        }

        throttle_pub->publish(throttle_msg);
        steering_pub->publish(steering_msg);

        // PUBLICAR SCAN PROCESADO
        auto new_scan = *scan_msg;
        new_scan.ranges = ranges;
        processed_scan_pub->publish(new_scan);

        // VISUALIZAR DIRECCIÓN (Flecha roja)
        visualization_msgs::msg::Marker marker;
        marker.header.frame_id = scan_msg->header.frame_id;
        marker.header.stamp = this->now();
        marker.ns = "direction";
        marker.id = 0;
        marker.type = visualization_msgs::msg::Marker::ARROW;
        marker.action = visualization_msgs::msg::Marker::ADD;
        marker.pose.position.x = 0.0;
        marker.pose.position.y = 0.0;
        marker.pose.position.z = 0.0;
        marker.pose.orientation.z = sin(angle / 2.0);
        marker.pose.orientation.w = cos(angle / 2.0);
        marker.scale.x = 1.0;
        marker.scale.y = 0.1;
        marker.scale.z = 0.1;
        marker.color.a = 1.0;
        marker.color.r = 1.0;
        marker.color.g = 0.0;
        marker.color.b = 0.0;

        marker_pub->publish(marker);
    }

    rclcpp::Publisher<std_msgs::msg::Float32>::SharedPtr throttle_pub;
    rclcpp::Publisher<std_msgs::msg::Float32>::SharedPtr steering_pub;
    rclcpp::Publisher<sensor_msgs::msg::LaserScan>::SharedPtr processed_scan_pub;
    rclcpp::Publisher<visualization_msgs::msg::Marker>::SharedPtr marker_pub;
    rclcpp::Subscription<sensor_msgs::msg::LaserScan>::SharedPtr scan_sub;
};

int main(int argc, char **argv) {
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<ReactiveFollowGap>());
    rclcpp::shutdown();
    return 0;
}
