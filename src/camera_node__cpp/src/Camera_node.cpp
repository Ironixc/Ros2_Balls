#include <opencv2/opencv.hpp>
#include <iostream>
#include <chrono>
#include <functional>
#include <memory>
#include <string>
#include <vector>
#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/image.hpp>
#include <std_msgs/msg/header.hpp>
#include <cv_bridge/cv_bridge.h>

using namespace std;

class CamPub : public rclcpp::Node
{
public:
    CamPub() : Node("camera_node")
    {
        this->declare_parameter<string>("source", "0");
        this->declare_parameter<double>("fps", 30.0);
        this->declare_parameter<int>("Lebar", 640);
        this->declare_parameter<int>("Tinggi", 480);

        string source_str = this->get_parameter("source").as_string();
        double fps = this->get_parameter("fps").as_double();
        int Lebar = this->get_parameter("Lebar").as_int();
        int Tinggi = this->get_parameter("Tinggi").as_int();

        publisher_ = this->create_publisher<sensor_msgs::msg::Image>("/camera/image_raw", 10);

        if (source_str.size() == 1 && isdigit(source_str[0])) {
            int cam_id = stoi(source_str);
            kamera_.open(cam_id, cv::CAP_V4L2);
            is_video_file_ = false;
        } else {
            kamera_.open(source_str);
            is_video_file_ = true;
        }
            kamera_.set(cv::CAP_PROP_FOURCC, cv::VideoWriter::fourcc('M', 'J', 'P', 'G'));
            kamera_.set(cv::CAP_PROP_FRAME_WIDTH, Lebar);
            kamera_.set(cv::CAP_PROP_FRAME_HEIGHT, Tinggi);
            kamera_.set(cv::CAP_PROP_FPS, fps);
        
        start_timer(fps);

        param_cb_handle_ = this->add_on_set_parameters_callback(
            std::bind(&CamPub::on_parameter_change, this, std::placeholders::_1));

        // RCLCPP_INFO(this->get_logger(), "Publishing at %.1f FPS", fps);
    }

private:
    void start_timer(double fps)
    {
        timer_ = this->create_wall_timer(
            std::chrono::duration<double>(1.0 / fps),
            std::bind(&CamPub::timer_callback, this));
    }

    rcl_interfaces::msg::SetParametersResult on_parameter_change(
        const std::vector<rclcpp::Parameter> & params)
    {
        rcl_interfaces::msg::SetParametersResult result;
        result.successful = true;

        for (const auto & p : params) {
            if (p.get_name() == "fps") {
                double new_fps = p.as_double();
                start_timer(new_fps);
                kamera_.set(cv::CAP_PROP_FPS, new_fps);
                RCLCPP_INFO(this->get_logger(), "FPS diubah menjadi %.1f", new_fps);
            } 
            else if (p.get_name() == "Lebar") {
                int new_lebar = p.as_int();
                kamera_.set(cv::CAP_PROP_FRAME_WIDTH, new_lebar);
                RCLCPP_INFO(this->get_logger(), "Lebar frame diubah menjadi %d", new_lebar);
            }
            else if (p.get_name() == "Tinggi") {
                int new_tinggi = p.as_int();
                kamera_.set(cv::CAP_PROP_FRAME_HEIGHT, new_tinggi);
                RCLCPP_INFO(this->get_logger(), "Tinggi frame diubah menjadi %d", new_tinggi);
            }
        }
        return result;
    }

    void timer_callback()
    {
        cv::Mat frame;
        kamera_ >> frame;


        std_msgs::msg::Header header;
        header.stamp = this->now();
        header.frame_id = "camera";

        auto msg = cv_bridge::CvImage(header, "bgr8", frame).toImageMsg();
        publisher_->publish(*msg);
        
        RCLCPP_INFO(this->get_logger(), "Publishing video frame");
    }

    cv::VideoCapture kamera_;
    bool is_video_file_{false};

    rclcpp::Publisher<sensor_msgs::msg::Image>::SharedPtr publisher_;
    rclcpp::TimerBase::SharedPtr timer_;
    rclcpp::node_interfaces::OnSetParametersCallbackHandle::SharedPtr param_cb_handle_;
};

int main(int argc, char * argv[])
{
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<CamPub>());
    rclcpp::shutdown();
    return 0;
}