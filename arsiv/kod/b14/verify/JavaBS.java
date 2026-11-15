import java.util.Arrays;

public class JavaBS {
    public static void main(String[] args) {
        int[] a = {1, 3, 5, 7};
        System.out.println("key=5 -> " + Arrays.binarySearch(a, 5));
        System.out.println("key=4 -> " + Arrays.binarySearch(a, 4));
        System.out.println("key=0 -> " + Arrays.binarySearch(a, 0));
        System.out.println("key=8 -> " + Arrays.binarySearch(a, 8));
        int[] b = {1, 2, 2, 2, 3};
        System.out.println("dup key=2 -> " + Arrays.binarySearch(b, 2));
    }
}
