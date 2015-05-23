package com.autosportlabs.racecapture;
import android.bluetooth.BluetoothAdapter;
import android.bluetooth.BluetoothDevice;
import android.bluetooth.BluetoothSocket;
import java.util.UUID;
import java.util.Set;
import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;


public class BluetoothConnection {
	BluetoothSocket socket;
	InputStream recv_stream;
	OutputStream send_stream;
	BufferedReader reader;
	
	static BluetoothConnection g_instance;
	
	private BluetoothConnection(){
	}
	
	static public BluetoothConnection createInstance(){
		if (g_instance == null){
			g_instance = new BluetoothConnection();
		}
		return g_instance;
	}
	
	public void open(String port){
		String error_message = null;
        try{
        	Set<BluetoothDevice> paired_devices = BluetoothAdapter.getDefaultAdapter().getBondedDevices();
            BluetoothSocket socket = null;
            for (BluetoothDevice device: paired_devices){
                if (device.getName() == port){
                    socket = device.createRfcommSocketToServiceRecord(UUID.fromString("00001101-0000-1000-8000-00805F9B34FB"));
                    break;
                }
            }
            if (socket != null){
                socket.connect();
                this.socket = socket;
                this.recv_stream = socket.getInputStream();
                this.send_stream = socket.getOutputStream();
                this.reader = new BufferedReader(new InputStreamReader(this.recv_stream,"UTF-8"));                
            }
            else{
                error_message = "Could not detect device " + port;
            }
        }
        catch(Exception e){
            error_message = "Error opening Bluetooth socket: " + e.getMessage();
        }

        if (error_message != null){
            throw new RuntimeException(error_message);
        }
            
        if (this.socket == null){
            throw new RuntimeException("Timed out opening Bluetooth port");
        }
	}
	
	public void close(){
        try{
            this.socket.close();
        }
        catch (Exception e){
            throw new RuntimeException("Error closing Bluetooth socket: " + e.getMessage());        	
        }
        finally{
            this.socket = null;
            this.recv_stream = null;
            this.send_stream = null;
            this.reader = null;
        }
	}
	
	public String readLine(){
		try{
			String line = this.reader.readLine();
			return line;
		}
		catch(IOException e){
			throw new RuntimeException("Error reading line: " + e.getMessage());
		}
	}
	
	public void write(String data){
		try{
			this.send_stream.write(data.getBytes());
		}
		catch(IOException e){
			throw new RuntimeException("Error writing: " + e.getMessage());
		}
	}
}
