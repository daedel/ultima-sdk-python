"""Simple example showing how to read radar colors from the SDK."""

from ultima_sdk.radar_col import RadarCol


def main():
    RadarCol.initialize()
    # Print first 16 radar colors as hex values
    for i in range(16):
        color = RadarCol.get_color(i)
        print(f"Index {i}: 0x{color:04X}")


if __name__ == "__main__":
    main()
